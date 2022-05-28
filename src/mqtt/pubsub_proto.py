"""
*TL;DR
Interaction between mqtt client and a class that receives
pubsub topic message notifications (a PubsubHandler)
"""

from typing import Protocol
from abc import abstractmethod

class PubsubHandler(Protocol):
    """Calls the mqtt client performs on the PubsubHandler to deliver notifications"""

    @abstractmethod
    def pubsub_connected(self, client):
        """When mqtt client connects
            client:
                mqtt client instance so clients can save it
        """
        raise NotImplementedError

    def pubsub_error(self, desc, data):
        """When an error notification is received from the mqtt library
            desc:
                error description
            data:
                error data details
        """
        raise NotImplementedError

class PubsubClient(Protocol):
    """Calls the PubsubHandler can perform on the mqtt client"""

    @abstractmethod
    def pubsub_last_will_set(self, lastwill_msg):
        """Set last will message; If the client disconnects without calling disconnect(),
           the broker will publish the message on its behalf.
            lastwill_msg : PubsubMessage
                message (topic, payload) to publish
        """
        raise NotImplementedError

    @abstractmethod
    def pubsub_message_handler_add(self, topic, handler, include_subtopics=False):
        """Subscribes to topic and adds a message handler for messages received
            topic:
                the topic to subscribe
            handler:
                the handler callback to be used. received a PubsubMessage.
        """
        raise NotImplementedError

    @abstractmethod
    def pubsub_message_handler_remove(self, topic):
        """unsubscribes to topic and removes message handler
            topic:
                the topic to subscribe
        """
        raise NotImplementedError

    @abstractmethod
    def pubsub_message_publish(self, pubsub_msg):
        """Publish a message
            pubsub_msg : PubsubMessage
                message (topic, payload) to publish
        """
        raise NotImplementedError
