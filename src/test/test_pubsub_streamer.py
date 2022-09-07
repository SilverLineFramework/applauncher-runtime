import unittest
import random
import string
import os
import threading 
import docker

from pubsub.pubsub_streamer import PubsubStreamer
from pubsub.listner import MQTTListner
from pubsub import PubsubMessage, PubsubHandler
from common import settings

class TestStreamer(unittest.TestCase, PubsubHandler):
    
    _CTN_IMG = "alpine"
    _CTN_NAME = "test_ctn"
    _CTN_CMD = '/bin/sh -c "cat"' # cat will echo back stdin
    
    _MAX_READ_BYTES = 1024
    
    _TOPICS = {'stdin': 'test/stdin', 'stdout': 'test/stdout', 'stderr': 'test/stderr'}
    
    @classmethod
    def setUpClass(self):
        # get docker client and image
        client = docker.from_env()
        client.images.pull(self._CTN_IMG)
        # stop (and remove; auto_remove=True) if container exists
        try:
            self.ctn = client.containers.get(self._CTN_NAME)
        except docker.errors.NotFound:
            # start detached container for testing (similar to what a docker launcher does)
            self.ctn = client.containers.run(self._CTN_IMG, 
                                         name=self._CTN_NAME, 
                                         auto_remove=True, 
                                         command=self._CTN_CMD, 
                                         stdin_open = True, 
                                         detach=True)
        self.ctn_sock = self.ctn.attach_socket(params={"stdin": 1, "stdout": 1, "stream":1})
        self.mqttc = MQTTListner(self, error_topic=settings.topics.get('dbg'), **settings.get('mqtt'))
        self.pubsub_connected_evt = threading.Event()
        self.pubsub_out_received_evt = threading.Event()

    def pubsub_connected(self, listner):
        # subscribe output topic to check container output
        self.mqttc.message_handler_add(self._TOPICS['stdout'], self.ctn_output)
        self.pubsub_connected_evt.set()

    def pubsub_error(self, desc: str, data: str):
        raise Exception(f"Pubsub error: {str}; {data}")
        
    def ctn_output(self, msg: PubsubMessage) -> None:
        self.received_msg_payload = msg.payload
        self.pubsub_out_received_evt.set()
    
    def test_container_direct_io(self):
        """ test direct io with container """
        test_str = ''.join(random.choices(string.ascii_lowercase, k=random.randint(100, self._MAX_READ_BYTES)))
        # write a string to container
        os.write(self.ctn_sock.fileno(), test_str.encode())
        # read from container
        read_bytes = os.read(self.ctn_sock.fileno(), self._MAX_READ_BYTES)
        # bytes read from container have a header that we remove
        read_bytes = PubsubStreamer.remove_header(read_bytes)
        read_str = read_bytes.decode()
        # sent and received should match (cat is echoing back)
        self.assertMultiLineEqual(read_str, test_str)
        pass
    
    def test_streamer(self):
        """ test io using pubsub streamer """
        # wait until we are connected
        evt_flag = self.pubsub_connected_evt.wait(5)
        if not evt_flag:
            raise Exception("Timeout waiting pubsub connection.")        

        test_str = ''.join(random.choices(string.ascii_lowercase, k=random.randint(100, self._MAX_READ_BYTES)))        

        # setup streamer
        ps_streamer = PubsubStreamer(self.mqttc, self.ctn_sock, self._TOPICS)
        # simulate we received a message on pubsub; send to container
        ps_streamer.input(PubsubMessage(self._TOPICS['stdin'], test_str))
        # wait to receive payload back on pubsub
        evt_flag = self.pubsub_out_received_evt.wait(5)
        if not evt_flag:
            raise Exception("Timeout waiting for message on output.")
        self.assertMultiLineEqual(self.received_msg_payload, test_str)
        
    @classmethod
    def tearDownClass(self):
        # stop (and remove; auto_remove=True) container
        self.ctn.stop()

if __name__ == '__main__':
    unittest.main()
