"""
*TL;DR
Get a stream from a socket in/out of pubsub
"""

import threading
import socket
import os

from pubsub import PubsubListner
from pubsub_msg import PubsubMessage

class PubsubStreamer:
    """
        Get streams from a socket in/out of pubsub
            Arguments
            ---------
            mqttc:
                a PubsubListner 
            sock:
                input/output socket;
                output = read from socket, publish to mqtt
                input = read from mqtt, write to socket
            out_topic:
                topic where to send the output
            in_topic:
                topic where to get the input
            remove_header:
                remove tailing header in received output
            encode_decode:
                assume strings in input/out: performs encode/decode
    """
    def __init__(self, 
                 mqttc: PubsubListner, 
                 sock: socket.SocketIO, 
                 out_topic: str = "out", 
                 in_topic: str = "in",
                 remove_header: bool = True,
                 encode_decode: bool = True) -> None:
        self._sock = sock
        self._mqttc = mqttc
        self._out_topic = out_topic 
        self._in_topic = in_topic 
        self._remove_header = remove_header
        self._encode_decode = encode_decode
        
        # create thread to start streaming 
        read_thread = threading.Thread(target=self.output)
        read_thread.start()
        
        # subscribe to topic and add handler to route messages to socket
        self._mqttc.pubsub_message_handler_add(self._in_topic, self.input)
        
    def output(self) -> None:
        """ Read output from socket, publish to mqtt """
        read_bytes = os.read(self._sock.fileno(),10000)
        if self._remove_header:
            read_bytes = self.remove_header(read_bytes)
        while read_bytes:
            if self._encode_decode:
                read_bytes = read_bytes.decode()
            self._mqttc.pubsub_message_publish(PubsubMessage(self._out_topic, read_bytes))
            read_bytes = os.read(self._sock.fileno(),10000)
            if self._remove_header:
                read_bytes = self.remove_header(read_bytes)
            
    def input(self, msg: PubsubMessage) -> None:
        """ Receive input msgs from mqtt, output to socket """
        data = msg.payload
        if self._encode_decode:
            data = msg.payload.encode()
        os.write(self._sock.fileno(),data)

    @classmethod
    def remove_header(self, input_bytes):
        """ Utility function to remove header from input received """
        return input_bytes[8:]
        