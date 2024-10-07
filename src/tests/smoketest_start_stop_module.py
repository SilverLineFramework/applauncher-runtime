"""
*TL;DR
These smoke tests are intended to be a simple end-to-end check
They are written to be somewhat self-contained 
(config is included in the test, msg formats)
"""
import unittest
import time
import subprocess
import threading
import re 

from model import *
from runtime import RuntimeMngr
from pubsub.listner import MQTTListner

# runtime config as it would come from config files 
RT_CFG = {
        "runtime": {
            "uuid": "cb65196b-0537-4364-939a-87d004babd4c",
            "tags": [
                "arena-py",
                "containerized-modules"
            ],
            "is_orchestration_runtime": False,
            "realm": "realm",
            "max_nmodules": 100,
            "reg_fail_error": False,
            "reg_timeout_seconds": 5,
            "reg_attempts": 1,
            "namespace": "public",
            "apis": "python:python3",
            "runtime_type": "containerized-modules",
            "name": "arena-rt1",
            "ka_interval_sec": 20
        },
        "mqtt": {
            "ssl": True,
            "port": 8883,
            "host": "broker.hivemq.com"
        },
        "topics": {
            "mio": "realm/s/{namespaced_scene}/p/{module_uuid}",
            "modules": "realm/s/+/+/p/+",
            "runtimes": "realm/g/public/p/cb65196b-0537-4364-939a-87d004babd4c"
        }
}


class TestRuntimeMngr(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # fixed uuids and names for testing
        self.rt_uuid = RT_CFG.get("runtime").get("uuid")
        self.mod_uuid = "928b6df3-48ab-4b7e-9174-47351aeee0bc"
        self.mod_name = 'pytest47351aeee0bc' # note: must be a normalized name (like python packages)
        self.ctnr_name = re.sub('[^A-Za-z0-9]+', '', self.mod_uuid) # assumes this is what launcher does 

        # instanciate a topics object to create repeatable topics for testing 
        self.topics = RuntimeTopics(attr_replace=None, **RT_CFG.get("topics"))

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
                                                        "scene": "public/default",
                                                        "file": "pytest.py",
                                                        "location": "arena/py/pytestenv",
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
        self.rtmngr = RuntimeMngr(**RT_CFG)
        
        self.mqttc = MQTTListner(self.rtmngr, **RT_CFG.get('mqtt'))
        
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
        # check if container is running using docker cli
        popen_result = str(subprocess.Popen(f"docker ps -f name={self.ctnr_name}", shell=True, stdout=subprocess.PIPE).stdout.read())
        self.assertGreaterEqual(popen_result.find(self.ctnr_name), 0)
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

        ## check if container is no longer running using docker cli
        popen_result = str(subprocess.Popen(f"docker ps -f name={self.ctnr_name}", shell=True, stdout=subprocess.PIPE).stdout.read())
        self.assertLess(popen_result.find(self.ctnr_name), 0)
        
    @classmethod
    def tearDownClass(self):
        self.rtmngr.exit()

if __name__ == '__main__':
    unittest.main()
