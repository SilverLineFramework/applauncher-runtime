import unittest

from model import *
from runtime import RuntimeMngr

class TestRuntimeMngr(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # instanciate a topics object to create repeatable topics for testing 
        self.topics = RuntimeTopics(
                                    runtimes="realm/proc/runtimes",
                                    modules="realm/proc/modules/c950272a-905b-4cc3-8b2d-c38a779806ef", 
                                    io="realm/proc/io/c950272a-905b-4cc3-8b2d-c38a779806ef",
                                    keepalive="realm/proc/keepalive/c950272a-905b-4cc3-8b2d-c38a779806ef")
        
        # instantiate a runtime manager for testing
        self.rtmngr = RuntimeMngr(runtime_topics = self.topics, uuid="c950272a-905b-4cc3-8b2d-c38a779806ef")
        
        # instantiate a python module for testing 
        self.module = Module(io_base_topic = self.topics.io, uuid='070aebda-390c-4529-b6ea-730eede590a8', name='test_mod', filename='arena/image-switcher', filetype='PY')
        
    def test_module_create_starts_new_module(self):
        # create request message as it would be received
        
        mod_req_msg_payload = { "object_id": uuid.uuid4(), "action": "create", "type": "arts_req", "data": { "type": "module", "uuid": "070aebda-390c-4529-b6ea-730eede590a8", "name": "test-mod", "parent": "f87abed2-de27-4745-95d3-553745568961", "filename": "arena/image-switcher", "filetype": "PY", "apis": ["wasm", "wasi"], "args": [], "env": [], "channels": [], "peripherals": [], "resources": None, "fault_crash": "ignore", "status": "A"}}
        mod_req_pubsub_msg = PubsubMessage(self.topics.modules, mod_req_msg_payload)
        
        # TODO
        pass        
if __name__ == '__main__':
    unittest.main()
