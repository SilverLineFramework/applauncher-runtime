import unittest

from model import *

class TestSlMsgs(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # instanciate a topics object to create repeatable topics for testing 
        self.topics = RuntimeTopics(
                                    runtimes="realm/proc/runtimes",
                                    modules="realm/proc/modules/c950272a-905b-4cc3-8b2d-c38a779806ef", 
                                    io="realm/proc/io/c950272a-905b-4cc3-8b2d-c38a779806ef",
                                    keepalive="realm/proc/keepalive/c950272a-905b-4cc3-8b2d-c38a779806ef")
        # instantiate a runtime for testing
        self.runtime = Runtime(topics=self.topics, uuid='c950272a-905b-4cc3-8b2d-c38a779806ef', name='test_rt', runtime_type=RuntimeLauncherTypes.module_container, max_nmodules=10, apis=["python:python3"])
        # instantiate a python module for testing 
        self.module = Module(io_base_topic = self.topics.io, uuid='070aebda-390c-4529-b6ea-730eede590a8', name='test_mod', filename='arena/image-switcher', filetype='PY')
        
    def test_runtime_register_message_is_correct(self):
        # create register message
        msg = self.runtime.create_runtime_msg()
        
        # expected payload/topic is based on setup (setUpClass) and uses msg object id which is created for each message
        expected_payload = {'object_id': msg.payload['object_id'], 'action': 'create', 'type': 'runtime_req', 'data': {'name': 'test_rt', 'runtime_type': 'module-container', 'max_nmodules': 10, 'apis': ['python:python3'], 'uuid': 'c950272a-905b-4cc3-8b2d-c38a779806ef', 'type': 'runtime'}}
        expected_topic = 'realm/proc/runtimes'
        
        assert (expected_topic == msg.topic)
        assert (expected_payload == msg.payload)

    def test_module_create_confirmation_message_is_correct(self):
        # create request message as it would be received
        sl_msgs = SlMsgs()
        req_msg = sl_msgs.req(self.topics.modules, 'create', self.module)
        # get confirmation msg
        confirm_msg = self.runtime.confirm_module_msg(req_msg)
        
        # expected payload/topic is based on setup (setUpClass) and expected object_id is the same as the request message
        expected_payload = {'object_id': req_msg.payload['object_id'], 'type': 'runtime_resp', 'data': {'result': 'ok', 'details': {'name': 'test_mod', 'filename': 'arena/image-switcher', 'filetype': 'PY', 'uuid': '070aebda-390c-4529-b6ea-730eede590a8', 'type': 'module'}}}
        expected_topic = 'realm/proc/modules/c950272a-905b-4cc3-8b2d-c38a779806ef'
        
        assert (expected_topic == confirm_msg.topic)
        assert (expected_payload == confirm_msg.payload)
        
if __name__ == '__main__':
    unittest.main()
