"""Runtime message handlers according to config topic dict keys"""

from logzero import logger
import uuid
import threading
import time
import atexit
from common.messages import FileTypes, Result
from .runtime import Runtime
from common.config import settings
from mqtt.pubsub_proto import PubsubHandler

class RuntimeMngr(PubsubHandler):
    """Runtime Manager; handles topic messages"""

    def __init__(self, module_launcher=None):
        self.modules = [] # list of modules
        self.moduleLauncher = module_launcher

        rt_settings = {**settings.get('runtime'), 'topics': settings.get('topics')}
        self.rt = Runtime(**rt_settings)

        # register exit handler to send delete runtime request
        atexit.register(self.exit_handler)

    def exit_handler(self):
        if hasattr(self, lastwill_msg):
            self.pubsub_client.pubsub_message_publish(self.lastwill_msg)
            time.sleep(.5) # need time to publish

    def pubsub_connected(self, client):
        self.pubsub_client = client

        # set last will; sent if we dont disconnect properly
        self.lastwill_msg = self.rt.unregister_req()
        self.pubsub_client.pubsub_last_will_set(self.lastwill_msg)

        # subscribe to reg to receive registration confirmation
        self.pubsub_client.pubsub_message_handler_add(self.rt.reg_topic, self.reg)

        # start a thread to send registration messages once we are connected
        self.reg_event = threading.Event()
        self.reg_thread = threading.Thread(target=self._register_runtime,
            args=(
                self.rt.register_req(),
                settings.get('runtime.reg_timeout_seconds'),))
        self.reg_thread.start()

    def pubsub_error(self, desc, data):
        pass

    def _register_runtime(self, reg_msg, timeout):
        """Register thread; sends register messages every timeout interval
           until register event is set"""

        while True:
            logger.info("[Runtime.register] Attempting to register...");
            self.pubsub_client.pubsub_message_publish(reg_msg)
            time.sleep(timeout)
            evt_flag = self.reg_event.wait(timeout)
            if evt_flag: break # event is set; registration response received

        # remove subscription to reg topic
        self.pubsub_client.pubsub_message_handler_remove(self.rt.reg_topic)

        # subscribe to runtime control topic to receive module requests
        self.pubsub_client.pubsub_message_handler_add(self.rt.ctl_topic, self.control)

        # subscribe to runtime stdin topic (TODO: send things here)
        self.pubsub_client.pubsub_message_handler_add(self.rt.stdin_topic, self.control)

        logger.info("[Runtime.register] Registration done.");


    def reg(self, decoded_msg):
        msg_data = decoded_msg.get('data')
        if msg_data.get('result') == Result.ok:
            self.reg_event.set()

    """
    ********************************
    """

    def __create_module_ack(self, msg):
        """Send ACK after creating module."""

        """TODO"""

        return None

    def __create_module(self, msg):
        """Handle create message."""

        """TODO"""
        """
        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid), "create",
            ModuleSerializer(module, many=False).data)
        """
        return None

    def __delete_module(self, msg):
        """Handle delete message."""

        """TODO"""

        """
        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id,
                "send_to_runtime": send_rt})
        """

    def _create_module(self, module_uuid, module_name, fn='', fid='', ft=FileTypes.WA, args=[], env=[]):
        rt = list(filter(lambda i: i.uuid == module_uuid, self.modules))
        if rt:
            raise Exception('UUID {} already exists'.format(module_uuid))
        else:
            # create module
            module = Module(module_uuid, module_name, self.parent, fn, fid, ft, args, env)
            self.modules.append(Module(module_uuid, module_name))
            delMsg = ModulesView().json_req(module, Action.delete)
            try:
                self.moduleLauncher.run(module, self.parent.dbg_topic, self.parent.ctl_topic, delMsg)
            except Exception as e:
                self.delete(module.uuid, False)
                raise e
            return module

    def _read_modules(self, module_uuid):
        rt = list(filter(lambda i: i.uuid == module_uuid, self.modules))
        if rt:
            return rt[0]
        else:
            raise Exception('UUID {} not found'.format(module_uuid))

    def _update_module(self, module_uuid, module_name, fn='', fid='', ft=FileTypes.WA, args=[]):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_uuid, enumerate(self.modules)))
        if module_idx:
            i, module_to_update = module_idx[0][0], module_idx[0][1]
            self.modules[i] = Module(module_uuid, module_name)
        else:
            raise Exception('UUID {} not found'.format(module_uuid))

    def _update_module_obj(self, module_obj):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_obj.uuid, enumerate(self.modules)))
        if module_idx:
            i, module_to_update = module_idx[0][0], module_idx[0][1]
            self.modules[i] = module_obj
        else:
            raise Exception('UUID {} not found'.format(module_obj.uuid))

    def _delete_module(self, module_uuid, kill=True):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_uuid, enumerate(self.modules)))
        if module_idx:
            i, rt_to_delete = module_idx[0][0], module_idx[0][1]
            del self.modules[i]
            if (kill):
                self.moduleLauncher.kill(module_uuid)
        else:
            raise Exception('UUID {} not found'.format(module_uuid))

    def __exit_module(self, msg):
        """Module terminated."""

        """TODO"""

        return None

    def control(self, msg):
        """Handle control messages."""
        # arts_resp -> is a message we sent, should be ignored
        msg_type = msg.get('type')
        if msg_type == 'arts_resp':
            return None

        print("\n[Control] {}".format(msg.payload))

        if msg_type == 'runtime_resp':
            result = msg.get('data', 'result')
            if result == "no file":
                # Send the WASM/AOT file over
                return self.__create_module(msg, True)
            else:
                return self.__create_module_ack(msg)
        elif msg_type == 'arts_req':
            action = msg.get('action')
            if action == 'create':
                return self.__create_module(msg, False)
            elif action == 'delete':
                return self.__delete_module(msg)
            elif action == 'exited':
                return self.__exited_module(msg)
            else:
                raise messages.InvalidArgument('action', action)
        else:
            raise messages.InvalidArgument('type', msg_type)

    def keepalive(self, msg):
        """Handle keepalive message."""
        return None
