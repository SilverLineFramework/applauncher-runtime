import unittest
import time
import subprocess
import threading

from model import *
from common import settings
from runtime import RuntimeMngr
from pubsub.listner import MQTTListner

class TestRuntimeMngr(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # fixed uuids and names for testing
        self.rt_uuid = "41c7bf1f-9b8a-4b2a-9764-7fd160a98e66"
        self.mod_uuid = "928b6df3-48ab-4b7e-9174-47351aeee0bc"
        self.mod_name = 'pytest47351aeee0bc' # note: must be a normalized name (like python packages)
        # instanciate a topics object to create repeatable topics for testing 
        
        self.topics = RuntimeTopics(
                                    runtimes="realm/proc/runtimes",
                                    modules=f"realm/proc/modules/{self.rt_uuid}", 
                                    modules_root="realm/proc/modules", 
                                    io=f"realm/proc/io/{self.rt_uuid}",
                                    keepalive=f"realm/proc/keepalive/{self.rt_uuid}")
    
        self.module_create_msg = PubsubMessage(self.topics.modules, 
                                                {
                                                    "object_id": str(uuid.uuid4()),
                                                    "action": "create",
                                                    "type": "req",
                                                    "data": {
                                                        "type": "module",
                                                        "uuid": self.mod_uuid,
                                                        "name": self.mod_name,
                                                        "parent": self.rt_uuid,
                                                        "file": "arena/py/pytestenv/pytest.py",
                                                        "filetype": "PY",
                                                        "apis": ["wasm", "wasi"],
                                                        "args": [],
                                                        "env": [],
                                                        "channels": [],
                                                        "peripherals": [],
                                                        "resources": None,
                                                        "fault_crash": "ignore",
                                                        "status": "A",
                                                    },
                                                });

        self.module_delete_msg = PubsubMessage(self.topics.modules, 
                                                {
                                                    "object_id": str(uuid.uuid4()),
                                                    "action": "delete",
                                                    "type": "req",
                                                    "data": {
                                                        "type": "module",
                                                        "uuid": self.mod_uuid,
                                                        "name": "test-mod",
                                                        "parent": self.rt_uuid,
                                                    },
                                                });
                                                        
        # instantiate a runtime manager for testing
        self.rtmngr = RuntimeMngr(runtime_topics = self.topics, uuid=self.rt_uuid)
        
        self.mqttc = MQTTListner(self.rtmngr, **settings.get('mqtt'))
        
        # use runtime manager evt to wait for registration
        evt_flag = self.rtmngr.wait_reg(50) 
        if not evt_flag:
            raise Exception("Timeout waiting for registration.")

        # create the module; this simulates a message received on the control topic
        self.rtmngr.control(self.module_create_msg)

        # wait for module
        time.sleep(1)

        self.mod_running_evt = threading.Event()   
        
        print("Done init.")
                        
    def test_module_create_starts_new_module(self):
        # check if container is running using docker cli (relies on force_container_name option in appsettings)
        popen_result = str(subprocess.Popen(f"docker ps -f name={self.mod_name}", shell=True, stdout=subprocess.PIPE).stdout.read())
        self.assertGreaterEqual(popen_result.find(self.mod_name), 0)
        self.mod_running_evt.set()

    def test_module_receives_stdin_data(self):
        evt_flag = self.mod_running_evt.wait(10)
        if not evt_flag:
            print("Timeout waiting for module.")
            self.assertTrue(False)

        # delete the module; this simulates a message received on the control topic
        self.rtmngr.control(self.module_delete_msg)

        # wait for teardown (might require more time)
        while self.rtmngr.module_exists(self.mod_uuid):
            time.sleep(1)

        ## check if container is no longer running using docker cli (relies on force_container_name option in appsettings)
        popen_result = str(subprocess.Popen(f"docker ps -f name={self.mod_name}", shell=True, stdout=subprocess.PIPE).stdout.read())
        self.assertLess(popen_result.find(self.mod_name), 0)
        
    @classmethod
    def tearDownClass(self):
        self.rtmngr.exit()

if __name__ == '__main__':
    unittest.main()
