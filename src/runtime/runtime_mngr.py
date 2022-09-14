"""Runtime message handlers according to config topic dict keys"""

from logzero import logger
import uuid
import threading
import time
import atexit
from typing import Dict

from common import settings, InvalidArgument
from model.runtime_types import Result
from model.runtime_topics import RuntimeTopics
from model import Runtime, Module
from pubsub import PubsubHandler
from launcher import LauncherContext
from pubsub.pubsub import PubsubListner

class RuntimeMngr(PubsubHandler):
    """Runtime Manager; handles topic messages"""

    def __init__(self, runtime_topics: RuntimeTopics=RuntimeTopics(**settings.get('topics')), **kwargs):
        self.__modules: Dict[str, MngrModule] = {} # dictionary of MngrModules by module uuid
        self.__module_io_base_topic = runtime_topics.io
        
        # arguments passed in constructor will override settings
        runtime_args = {**settings.get('runtime'), **kwargs} 
        self.__rt = Runtime(topics=runtime_topics, **runtime_args)

        # register exit handler to send delete runtime request
        atexit.register(self.__exit_handler)

    def __exit_handler(self):
        
        # try to gracefully stop threads
        self.__reg_event.set() # in case we are still tyring to register
        self.__ka_exit.set()
        
        # publish last will before exit
        if hasattr(self, "lastwill_msg"):
            self.__pubsub_client.message_publish(self.__lastwill_msg)
            time.sleep(.5) # need time to publish

    def pubsub_connected(self, client):
        self.__pubsub_client = client

        # set last will; sent if we dont disconnect properly
        self.__lastwill_msg = self.__rt.delete_runtime_msg()
        self.__pubsub_client.last_will_set(self.__lastwill_msg)

        # subscribe to runtimes to receive registration confirmation
        self.__pubsub_client.message_handler_add(settings.topics.runtimes, self.reg)

        # start a thread to send registration messages once we are connected
        self.__reg_event = threading.Event()
        self.__reg_thread = threading.Thread(target=self.__register_runtime,
            args=(
                self.__rt.create_runtime_msg(),
                settings.get('runtime.reg_timeout_seconds', 5),
                settings.get('runtime.reg_attempts', 0),))
        self.__reg_thread.start()

    def pubsub_error(self, desc, data):
        logger.error(desc, data)
        pass

    def __keepalive(self, ka_interval_secs):
        """Keepalive thread; sends keepalive messages periodically """
        logger.info("Starting keepalive.")
        
        while True:
            # TODO: add stats
            #children = []
            #for module in self.__modules:
            #    mod_ka = module.keepalive_attrs({})
            #    children.append(mod_ka)
            exit_flag = self.__ka_exit.wait(ka_interval_secs)
            if exit_flag: break # event is set; exit
            
            #children = [mngr_mod.module.keepalive_attrs({}) for mngr_mod in self.__modules]
            children = [mngr_mod.module.keepalive_attrs({}) for _, mngr_mod in self.__modules.items()]
            keepalive_msg = self.__rt.keepalive_msg(children)
            logger.debug("Sending keepalive.")
            self.__pubsub_client.message_publish(keepalive_msg)
            
    def __register_runtime(self, reg_msg, timeout_secs, reg_attempts):
        """Register thread; sends register messages every timeout interval
           until register event is set"""

        while True:
            if reg_attempts > 0: 
                reg_attempts = reg_attempts - 1
                if reg_attempts == 0: break
            logger.info("Runtime attempting to register...");
            self.__pubsub_client.message_publish(reg_msg)
            evt_flag = self.__reg_event.wait(timeout_secs)
            if evt_flag: break # event is set; registration response received

        # remove subscription to reg topic
        self.__pubsub_client.message_handler_remove(settings.topics.runtimes)

        # subscribe to runtime control topic to receive module requests
        self.__pubsub_client.message_handler_add(settings.topics.modules, self.control)
                    
        logger.info("Runtime registration done.");
        
        # start keepalive
        ka_interval_sec = self.__reg_details.get('ka_interval_sec')
        if ka_interval_sec:
            self.__ka_exit = threading.Event()
            self.__ka_thread = threading.Thread(target=self.__keepalive,
                args=(ka_interval_sec,))
            self.__ka_thread.start()
        
    def reg(self, decoded_msg):
        msg_data = decoded_msg.get('data')
        if msg_data.get('result') == Result.ok:
            self.__reg_details = msg_data.get('details', {})
            self.__reg_event.set()

    def control(self, msg):
        """Handle control messages."""
        # arts_resp -> is a message we sent, should be ignored
        msg_type = msg.get('type')
        if msg_type == 'arts_resp':
            return None

        print("\n[Control] {}".format(msg.payload))

        if msg_type == 'arts_req':
            action = msg.get('action')
            if action == 'create':
                return self.__create_module(msg.get('data'))
            elif action == 'delete':
                return self.__delete_module(msg.get('data', {}))
            #elif action == 'exited':
            #    return self.__exited_module(msg)
            else:
                raise InvalidArgument('action', action)
        else:
            raise InvalidArgument('type', msg_type)

    """
    ********************************
    """

    def __create_module_ack(self, mod):
        """Send ACK after creating module."""

        """TODO"""

        return None

    def __module_exit(self, mod_uuid):
        print(f"module {mod_uuid} exited")
         
    def __create_module(self, mod):
        """Handle create message."""

        print("HERE", mod)
        mod_uuid = mod.get('uuid')
        if mod_uuid: 
            if self.__modules.get(mod_uuid):
                raise InvalidArgument('uuid', 'Module {} already exists'.format(mod_uuid))
        module = Module(io_base_topic = self.__module_io_base_topic, **mod)

        self.__modules[module.uuid] = MngrModule(module, self.__pubsub_client)
        self.__modules[module.uuid].start_module(lambda: self.__module_exit(module.uuid))
        
        return None

    def __delete_module(self, mod):
        """Handle delete message."""

        """TODO"""

        """
        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id,
                "send_to_runtime": send_rt})
        """

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

    def start_module(self, on_module_exit_call):
        return self.module_launcher.start_module(on_module_exit_call)