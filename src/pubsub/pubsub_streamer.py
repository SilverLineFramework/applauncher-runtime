"""
*TL;DR
Get a stream from a socket in/out of pubsub
"""

import threading
import socket
import os
from typing import Dict
from enum import Enum
from logzero import logger

from pubsub.pubsub import PubsubListner
from .pubsub_msg import PubsubMessage
class Streams(str, Enum):
    """Streams enum."""
    stdout = 'stdout'
    stdin = 'stdin'
    stderr = 'stderr'

class PubsubStreamer:
    """
        Get streams from a socket in/out of pubsub
            Arguments
            ---------
            pubsubc:
                a PubsubListner 
            sock:
                input/output socket;
                output = read from socket, publish to mqtt
                input = read from mqtt, write to socket
            topics:
                dictionary of stdin (where to get the input to the container), stderr and stdout topics
            remove_header:
                remove tailing header in received output
            encode_decode:
                assume strings in input/out: performs encode/decode
    """
            
    # When docker multiplexes streams a byte in the header indicates: 1 = stdout; 2 = stderr
    _MULTIPLEXED_STREAMS = {
        1 : Streams.stdout,
        2 : Streams.stderr
    }
    
    def __init__(self, 
                 pubsubl: PubsubListner, 
                 sock: socket.SocketIO, 
                 topics: Dict = { Streams.stdin: 'in_topic', Streams.stdout: 'out_topic', Streams.stderr: 'err_topic'}, 
                 multiplexed: bool = True,
                 encode_decode: bool = True) -> None:
        self._sock = sock
        self._pubsub_client = pubsubl
        self._topics = topics
        self._multiplexed = multiplexed
        self._encode_decode = encode_decode
        
        logger.debug(f"Starting IO Streamer at {topics}")
        
        # create thread to start streaming stdout and stderr
        read_thread = threading.Thread(target=self.output)
        read_thread.start()
        
        # subscribe to stdin topic and add handler to route messages to socket
        self._pubsub_client.message_handler_add(self._topics.get(Streams.stdin), self.input)
                        
    def output(self) -> None:
        """ Read output from socket, publish to mqtt 
        
        Docker multiplexes streams when there is no PTY attached. 
        Data is sent with an 8-byte header, followed by a data payload.
        First 4 bytes: stream from which the data came (1 = stdout, 2 = stderr)
        Last 4 bytes: length of the following data payload
        """
        if self._multiplexed:
            header = os.read(self._sock.fileno(), 8)
            plen = int.from_bytes(header[4:8], byteorder='big')
            payload_bytes = os.read(self._sock.fileno(), plen)
        else: payload_bytes = os.read(self._sock.fileno(), 4096)
        while payload_bytes:
            if self._encode_decode:
                payload_bytes = payload_bytes.decode()
            out_topic = self._topics.get(Streams.stdout)
            if self._multiplexed:
                # publish to stdout or stderr topic according to first byte in the header
                out_topic = self._topics.get(PubsubStreamer._MULTIPLEXED_STREAMS.get(header[0], Streams.stdout))
            self._pubsub_client.message_publish(PubsubMessage(out_topic, payload_bytes))
            if self._multiplexed:
                header = os.read(self._sock.fileno(), 8)
                plen = int.from_bytes(header[4:8], byteorder='big')
                payload_bytes = os.read(self._sock.fileno(), plen)
            else: payload_bytes = os.read(self._sock.fileno(), 4096)

        logger.debug(f"Streammer for {self._topics} **cleanup**.")
        self._pubsub_client.message_handler_remove(self._topics.get(Streams.stdin))            
            
    def input(self, msg: PubsubMessage) -> None:
        """ Receive input msgs from mqtt, output to socket """
        data = msg.payload
        if self._encode_decode:
            data = msg.payload.encode()
        os.write(self._sock.fileno(), data)

    @classmethod
    def remove_header(self, input_bytes):
        """ Utility function to remove header from input received """
        return input_bytes[8:]
        