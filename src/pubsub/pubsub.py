"""
*TL;DR
Interface between mqtt client and a class that receives
pubsub topic message notifications (a PubsubHandler)
"""

from typing import Protocol, Callable
from abc import abstractmethod

from .pubsub_msg import PubsubMessage

class PubsubListner(Protocol):
    """Calls the PubsubHandler can perform on the mqtt listner"""

    @abstractmethod
    def last_will_set(self, lastwill_msg: PubsubMessage) -> None:
        """Set last will message; If the client disconnects without calling disconnect(),
           the broker will publish the message on its behalf.
            lastwill_msg : PubsubMessage
                message (topic, payload) to publish
        """
        raise NotImplementedError

    @abstractmethod
    def message_handler_add(self,
                                    topic: str,
                                    handler: Callable[[PubsubMessage], None],
                                    json_decode: bool=True,
                                    ) -> None:
        """Subscribes to topic and adds a message handler for messages received
            topic:
                the topic to subscribe
            handler:
                the handler callback to be used. Receives a PubsubMessage.
            json_decode:
                decode json message
        """
        raise NotImplementedError

    @abstractmethod
    def message_handler_remove(self, topic: str) -> None:
        """unsubscribes to topic and removes message handler
            topic:
                the topic to subscribe
        """
        raise NotImplementedError

    @abstractmethod
    def message_publish(self, pubsub_msg: PubsubMessage) -> None:
        """Publish a message
            pubsub_msg : PubsubMessage
                message (topic, payload) to publish
        """
        raise NotImplementedError

class PubsubHandler(Protocol):
    """Calls the mqtt listner performs on the PubsubHandler to deliver notifications"""

    @abstractmethod
    def pubsub_connected(self, client: PubsubListner):
        """When mqtt listner connects
            client:
                mqtt listner instance if handler wants to save it
        """
        raise NotImplementedError

    @abstractmethod
    def pubsub_error(self, desc: str, data: str):
        """When an error notification is received from the mqtt library
            desc:
                error description
            data:
                error data details
        """
        raise NotImplementedError