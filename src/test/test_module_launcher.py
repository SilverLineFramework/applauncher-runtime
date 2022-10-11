import unittest
import threading 
import subprocess
from logzero import logger

from launcher.launcher import LauncherContext
from model import Module
from common import settings
from pubsub import MQTTListner, PubsubMessage
class TestLauncher(unittest.TestCase):
    
    # fixed module uuid so topics are also fixed
    _MOD_UUID = 'a541057d-429f-46f3-b154-c38285c4ed33'

    # fixed module name; some name that does not conflict with ofther containers
    _MOD_NAME = 'pytest-c38285c4ed33'
    
    # topics based on above uuid
    #_RUNTIME_DBG_TOPIC = "realm/proc/debug/94d4dc1b-b2bb-4207-9778-d96b16052475"
    

    @classmethod
    def setUpClass(self):
        # instantiate a python module for testing
        self.module = Module(uuid=self._MOD_UUID, name=self._MOD_NAME, filename='arena/py/pytestenv/pytest.py', filetype='PY')
        self.mqttc = MQTTListner(pubsub_handler=self, error_topic=settings.topics.io, **settings.get('mqtt'))
        
        self.pubsub_connected_evt = threading.Event()        
        self.pubsub_out_received_evt = threading.Event()
        
        # kill test container just in case
        popen_result = str(subprocess.Popen(f"docker kill {self._MOD_NAME} 2>/dev/null", shell=True, stdout=subprocess.PIPE).stdout.read())

    def pubsub_connected(self, listner):
        # subscribe output topic to check container output
        self.mqttc.message_handler_add(self.module.topics.get('stdout'), self.ctn_output)
        self.pubsub_connected_evt.set()

    def pubsub_error(self, desc: str, data: str):
        raise Exception(f"Pubsub error: {str}; {data}")

    def on_module_exit(self):
        print(f"Module stopped {self.module.name}.")

    def ctn_output(self, msg: PubsubMessage) -> None:
        self.received_msg_payload = msg.payload
        # look for one of the fruits printed by the test program
        if msg.payload == "Apple\n":
            self.pubsub_out_received_evt.set() # we found it! test is done

    def test_python_launcher(self):
        # wait until we are connected
        evt_flag = self.pubsub_connected_evt.wait(5)
        if not evt_flag:
            logger.error("Timeout waiting for mqtt connection.")
            self.assertTrue(False)
            
        # setup launcher, force container name to match module name
        mod_launcher = LauncherContext.get_launcher_for_module(self.module, force_container_name=True, pubsubc=self.mqttc)
        mod_launcher.start_module(self.on_module_exit)
        
        # check if container is running using docker cli
        popen_result = str(subprocess.Popen(f"docker ps -f name={self._MOD_NAME}", shell=True, stdout=subprocess.PIPE).stdout.read())
        
        self.assertTrue(popen_result.find(self._MOD_NAME))

        stats = mod_launcher.get_stats()
        print("Stats:", stats)
        
        # wait to receive expected output from container
        evt_flag = self.pubsub_out_received_evt.wait(15)
        if not evt_flag:
            logger.error("Timeout waiting for container output.")
            mod_launcher.stop_module()
            self.assertTrue(False)
        
        mod_launcher.stop_module()

if __name__ == '__main__':
    unittest.main()
