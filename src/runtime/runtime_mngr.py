"""
   Runtime manager keeps a list of modules and handles pubsub messages (create/delete modules) according 
   to config topic dict keys
   Once it receives pubsub connection notification, it starts tryting to register the runtime
   
   NOTE/TODO: We will register again everytime we lose mqtt connection (we are retrying to connect)
"""
from logzero import logger
import uuid
import threading
import time
import atexit
from typing import Dict

from common import settings, InvalidArgument
from model import Result, RuntimeTopics
from model import Runtime, Module, MessageType, Action
from pubsub import PubsubHandler
from launcher import LauncherContext
from pubsub import PubsubListner, PubsubMessage
from common.exception import MissingField, RuntimeException, LauncherException

class RuntimeMngr(PubsubHandler):
    """Runtime Manager; handles topic messages"""

    def __init__(self, runtime_topics: RuntimeTopics=RuntimeTopics(**settings.get('topics')), **kwargs):
        self.__modules: Dict[str, MngrModule] = {} # dictionary of MngrModules by module uuid
        self.__modules_lock = threading.Lock()
        self.__runtime_topics = runtime_topics
        self.__lastwill_msg = None
        self.__conn_event = threading.Event()
        self.__reg_event = threading.Event()
        self.__ka_exit = threading.Event()
        self.__pending_delete_msgs: Dict[str, PubsubMessage] = {} # dictionary messages waiting module exit notification
        self.__exited=False;

        # arguments passed in constructor will override settings
        runtime_args = {**settings.get('runtime'), **kwargs} 
        self.__rt = Runtime(topics=runtime_topics, **runtime_args)

        # register exit handler to send delete runtime request
        atexit.register(self.__exit_handler)

    def __exit_handler(self):
        """ Exit handler; do some cleanup """
        if self.__exited: return
                
        # try to gracefully stop threads
        self.__reg_event.set() # in case we are still trying to register
        self.__ka_exit.set()
        
        # stop containers
        with self.__modules_lock:
            for (_, mod) in self.__modules.items():
                mod.stop()
        
        # publish last will before exit
        if self.__lastwill_msg != None:
            self.__pubsub_client.message_publish(self.__lastwill_msg)
            time.sleep(.5) # need time to publish
        
        self.__exited=True;

    def exit(self):
        self.__exit_handler()
        self.__pubsub_client.disconnect()

    def pubsub_connected(self, client):
        """ Once we are connected on pubsub, try to to register 
            NOTE/TODO: We will register again everytime we lose mqtt connection (we are retrying to connect)
        """
        self.__conn_event.set() # signal event
        self.__pubsub_client = client
        
        # set last will; sent if we dont disconnect properly
        self.__lastwill_msg = self.__rt.delete_runtime_msg()
        self.__pubsub_client.last_will_set(self.__lastwill_msg)

        # subscribe to runtimes to receive registration confirmation
        self.__pubsub_client.message_handler_add(self.__rt.topics.runtimes, self.reg)

        reg_attempts = settings.get('runtime.reg_attempts')
        if reg_attempts < 0:
            # skip registration
            self.__register_runtime_done()
        else:
            # start a thread to send registration messages once we are connected
            self.__reg_thread = threading.Thread(target=self.__register_runtime_send,
                args=(
                    self.__rt.create_runtime_msg(),
                    settings.get('runtime.reg_timeout_seconds'),
                    settings.get('runtime.reg_attempts'),
                    settings.get('runtime.reg_fail_error')))
            self.__reg_thread.start()

    def pubsub_error(self, desc, data):
        logger.error(desc, data)

    def wait_reg(self, timeout_secs):
        evt_flag = self.__conn_event.wait(10)
        if not evt_flag:
            raise RuntimeException("timeout waiting for MQTT connection.", "Could not connect.") 
                 
        evt_flag = self.__reg_event.wait(timeout_secs)
        return evt_flag

    def __keepalive(self, ka_interval_secs):
        """Keepalive thread; sends keepalive messages periodically """
        logger.info("Starting keepalive.")
        
        while True:
            exit_flag = self.__ka_exit.wait(ka_interval_secs)
            self.__ka_exit.clear()
            if exit_flag: break # event is set; exit
            
            with self.__modules_lock:
                children = [mngr_mod.module.keepalive_attrs(mngr_mod.module_launcher.get_stats()) for _, mngr_mod in self.__modules.items()]
            keepalive_msg = self.__rt.keepalive_msg(children)
            logger.debug("Sending keepalive.")
            self.__pubsub_client.message_publish(keepalive_msg)
            
    def __register_runtime_send(self, reg_msg, timeout_secs, reg_attempts, reg_fail_error):
        """Register thread; sends register messages every timeout interval
           until register event is set"""

        reg_count = reg_attempts
        reg_flag = False
        while True:
            if reg_count > 0: 
                reg_count = reg_count - 1
                if reg_count == 0: break
            logger.info("Runtime attempting to register...");
            self.__pubsub_client.message_publish(reg_msg)
            reg_flag = self.wait_reg(timeout_secs)
            if reg_flag == True: break # event is set; registration response received
        
        if not reg_flag:
            if reg_fail_error: raise RuntimeException("runtime registration failed.", "Could not register runtime after {} attempts.".format(reg_attempts))
            else: 
                logger.info("No registration response after {} attempts.".format(reg_attempts))
                self.__reg_event.set()
         
        self.__register_runtime_done()
         
    def __register_runtime_done(self):
        """Finish registration; subscribes to topics and starts keepalive"""
        
        # remove subscription to reg topic
        self.__pubsub_client.message_handler_remove(self.__rt.topics.runtimes)

        # subscribe to runtime control topic to receive module requests
        self.__pubsub_client.message_handler_add(self.__rt.topics.modules, self.control)

        # subscribe to module request "broadcast", i.e the topic level above, usually meant for orchestrator
        modules_broadcast = "/".join(list(self.__rt.topics.modules.split('/')[0:-1]))
        self.__pubsub_client.message_handler_add(modules_broadcast, self.control)
                            
        # start keepalive
        ka_interval_sec = self.__rt.ka_interval_sec
        if ka_interval_sec:
            self.__ka_thread = threading.Thread(target=self.__keepalive,
                args=(ka_interval_sec,))
            self.__ka_thread.start()
            
        logger.info("Runtime registration done.")
                
    def reg(self, decoded_msg):
        msg_data = decoded_msg.get('data')
        if msg_data.get('result') == Result.ok:
            self.__reg_event.set()

    def control(self, msg):
        """Handle control messages."""

        # ignore messages from ourselfs
        try: 
            msg_from = msg.payload['from']
            if msg_from == self.__rt.uuid:
                return None
        except KeyError:
            pass

        logger.debug("\n[Control] {}".format(msg.payload))

        msg_type = msg.get('type')

        if msg_type == MessageType.request:
            action = msg.get('action')
            if action == Action.create:
                return self.__create_module(msg)
            elif action == Action.delete:
                return self.__delete_module(msg)
            else:
                raise InvalidArgument('action', action)
        else:
            raise InvalidArgument('type', msg_type)

    def module_exists(self, mod_uuid):
        try:
            self.__modules[mod_uuid]
        except KeyError:
            return False

        return True

    def __module_exit(self, mod_uuid):
        logger.debug(f"module {mod_uuid} exited")
        
        # check if this is due to a delete request
        delete_msg = None
        try:
            delete_msg = self.__pending_delete_msgs.pop(mod_uuid)
        except KeyError:
            pass

        module = None
        # remove module from our module list
        with self.__modules_lock:    
            try:
                module = self.__modules.pop(mod_uuid).module
            except KeyError as ke:
                raise RuntimeException("Error deleting", "Module {} is not known".format(mod_uuid)) from ke
            else:         
                delete_msg = self.__rt.delete_module_msg(module.delete_attrs())
        
        if delete_msg: self.__pubsub_client.message_publish(delete_msg)
        
    def __create_module(self, create_msg: PubsubMessage):
        """Handle create message."""

        mod = create_msg.get('data')

        # only care about messages with us as parent
        try:
            if mod['parent'] != self.__rt.uuid and mod['parent'] != self.__rt.name:
                raise InvalidArgument("parent", "Parent does not match this runtime")
        except KeyError:
            raise InvalidArgument("parent", "Parent is required")

        mod_uuid = mod.get('uuid')
        if mod_uuid: 
            with self.__modules_lock:
                if self.__modules.get(mod_uuid):
                    raise InvalidArgument("uuid", "Module {} already exists".format(mod_uuid))
            
        logger.info(f"Starting module {mod_uuid}.")
            
        module = Module(io_base_topic = self.__rt.topics.io, **mod)

        with self.__modules_lock:
            self.__modules[module.uuid] = MngrModule(module, self.__pubsub_client)
            self.__modules[module.uuid].start(lambda: self.__module_exit(module.uuid))

        # confirm create request
        return self.__rt.confirm_module_msg(create_msg)

    def __delete_module(self, delete_msg):
        """Handle delete message."""

        mod_uuid = delete_msg.get('data').get('uuid')
        if not mod_uuid: 
            raise MissingField("UIID field missing (trying to delete)")
        
        logger.info(f"Stopping module {mod_uuid}.")
        
        with self.__modules_lock:
            try:
                mod_mngr = self.__modules[mod_uuid]
            except KeyError as ke:
                raise InvalidArgument("uuid", "Module {} does not exist (trying to delete)".format(mod_uuid)) from ke

        # NOTE: a delete module will be sent by module exit handler
        try:
            mod_mngr.stop()
        except LauncherException:
            logger.warn("Module not running.")            
            self.__module_exit(mod_mngr.module.uuid)

        # save pending delete message to be sent later;
        # will be sent when a module exit notification is received
        # TODO: add some timeout mechanism
        self.__pending_delete_msgs[mod_uuid] = self.__rt.confirm_module_msg(delete_msg)
        
class MngrModule():
    """Keep a module instance and a module laucher for each module started"""        
    
    def __init__(self, module: Module, pubsubc: PubsubListner):
        """
            Arguments
            ---------
                module:
                    module object
                pubsubc:
                    a pubsub client object the module streamer uses to publish messages
        """
        self.module = module
        
        # setup launcher, force container name to match module name
        self.module_launcher = LauncherContext.get_launcher_for_module(module, pubsubc=pubsubc)

    def start(self, on_module_exit_call):
        return self.module_launcher.start_module(on_module_exit_call)
    
    def stop(self):
        self.module_launcher.stop_module()

