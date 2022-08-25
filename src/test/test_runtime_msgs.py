import unittest
import json
from types import SimpleNamespace

from common import settings
from model import Runtime, Module
import model.runtime_types as RuntimeTypes
from runtime.runtime_msgs import RuntimeMsgs

class TestRtMsgs(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # instantiate a runtime for testing
        self.runtime = Runtime(uuid='c950272a-905b-4cc3-8b2d-c38a779806ef', name='test_rt', runtime_type=RuntimeTypes.RuntimeLauncherTypes.module_container, max_nmodules=10, apis=["python:python3"])
        # instantiate a python module for testing 
        self.module = Module(uuid='070aebda-390c-4529-b6ea-730eede590a8', name='test_mod', filename='arena/image-switcher', filetype='PY')
        # instanciate an object from json to create repeatable topics for testing 
        topics_str = '{"reg": "realm/proc/reg", "ctl": "realm/proc/control/c950272a-905b-4cc3-8b2d-c38a779806ef", "runtimes": "realm/proc/runtimes", "modules": "realm/proc/modules/c950272a-905b-4cc3-8b2d-c38a779806ef", "dbg": "realm/proc/debug/c950272a-905b-4cc3-8b2d-c38a779806ef", "stdout": "realm/proc/debug/c950272a-905b-4cc3-8b2d-c38a779806ef/stdout", "stdin": "realm/proc/debug/c950272a-905b-4cc3-8b2d-c38a779806ef/stdin", "stderr": "realm/proc/debug/c950272a-905b-4cc3-8b2d-c38a779806ef/stderr"}'
        self.topics = json.loads(topics_str, object_hook=lambda d: SimpleNamespace(**d)) 
        # instanciate runtime msgs
        self.rt_msgs = RuntimeMsgs(self.topics)
        
    def test_runtime_register_message_is_correct(self):
        # create register message
        msg = self.rt_msgs.create_runtime(self.runtime)
        
        # expected payload/topic is based on setup (setUpClass) and uses msg object id which is created for each message
        expected_payload = {'object_id': msg.payload['object_id'], 'action': 'create', 'type': 'runtime_req', 'data': {'name': 'test_rt', 'runtime_type': 'module-container', 'max_nmodules': 10, 'apis': ['python:python3'], 'uuid': 'c950272a-905b-4cc3-8b2d-c38a779806ef', 'type': 'runtime'}}
        expected_topic = 'realm/proc/runtimes'
        
        assert (expected_topic == msg.topic)
        assert (expected_payload == msg.payload)

    def test_module_create_confirmation_message_is_correct(self):
        # create message
        req_msg = self.rt_msgs.req(self.topics.modules, 'create', self.module)
        confirm_msg = self.rt_msgs.confirm_module(req_msg)
        
        # expected payload/topic is based on setup (setUpClass) and expected object_id is the same as the request message
        expected_payload = {'object_id': req_msg.payload['object_id'], 'type': 'runtime_resp', 'data': {'result': 'ok', 'details': {'name': 'test_mod', 'filename': 'arena/image-switcher', 'filetype': 'PY', 'uuid': '070aebda-390c-4529-b6ea-730eede590a8', 'type': 'module'}}}
        expected_topic = 'realm/proc/modules/c950272a-905b-4cc3-8b2d-c38a779806ef'
        
        assert (expected_topic == confirm_msg.topic)
        assert (expected_payload == confirm_msg.payload)
        
if __name__ == '__main__':
    unittest.main()
