"""MQTT Client."""

import traceback
import json
import ssl as ssl_lib
from json.decoder import JSONDecodeError
from typing import Dict, Any, Callable
import uuid
import paho.mqtt.client as paho
from logzero import logger

from common import RuntimeException

from pubsub.pubsub_msg import PubsubMessage
from pubsub.pubsub import PubsubListner, PubsubHandler

class MQTTListner(paho.Client, PubsubListner):
    """MQTT client class extending mqtt.Client. Implements PubsubListner methods.

    Parameters
    ----------
    topic_handler: PubsubHandler
        send notifications (connected, error, topic messages) to topic_handler
    error_topic: str
        topic where errors are sent
    host: str
        MQTT host
    port: int
        MQTT port
    username: str
        MQTT user
    password: str
        MQTT password
    ssl: bool
        MQTT ssl connection
    cid : str
        Client ID for paho MQTT client.
    """

    __topic_dispatcher: Dict[str, Any]
    __subscribe_mid: Dict[int, str]
    
    def __init__(self,
                topic_handler: PubsubHandler,
                error_topic: str = 'error_topic',
                host: str = 'arenaxr.org',
                port: int = 1883,
                username: str = None,
                password: str = None,
                ssl: bool= False,
                cid: str= str(uuid.uuid4())) -> None:

        super().__init__(cid)

        self._error_topic = error_topic
        self.__topic_dispatcher = {}
        self.__subscribe_mid = {}

        logger.debug("Starting MQTT client...")

        
        self._th = topic_handler
        if not topic_handler:
            logger.info("No topic handler provided! MQTT notifications will not be delivered.")

        if username and password:
            self.username_pw_set(username=username, password=password)
        if ssl:
            self.tls_set(cert_reqs=ssl_lib.CERT_NONE)

        self.connect(host, port, 60)

        self.loop_start()

    def on_connect(self, mqttc, userctx, flags, rc) -> None:
        """Client connect callback."""
        if rc == 0:
            logger.debug("Connected.")
            if self._th:
                self._th.pubsub_connected(self._th, mqttc)
        else:
            logger.error(f"Bad connection returned code={rc}")

    def on_message(self, mqttc, userctx, msg) -> None:
        """MQTT Message handler."""

        res = self.__on_message(msg)
        # only publish if not `None`
        if res:
            payload = json.dumps(res.payload)
            print(f"[Response] {str(res.topic)}: {payload}")
            self.publish(res.topic, payload)

    def on_subscribe(self, mqttc, obj, mid, granted_qos) -> None:
        """Subscribe callback."""
        logger.debug(f"Subscribed: \
                    {self.__subscribe_mid.get(mid, 'to a topic.')}")

    def on_log(self, mqttc, obj, level, string) -> None:
        """Logging callback."""

        if level == paho.MQTT_LOG_ER:
            logger.error(f"MQTT Error: {string}")
            if self._th:
                self._th.pubsub_error(self._th, "MQTT Error", string)
            return
        if level == paho.MQTT_LOG_WARNING:
            logger.warning(string)
        elif level == paho.MQTT_LOG_INFO:
            logger.info(string)
        else: logger.debug(string)

    def last_will_set(self, lastwill_msg: PubsubMessage) -> None:
        """Set last will message; If the client disconnects without calling disconnect(),
           the broker will publish the message on its behalf.
            lastwill_msg : PubsubMessage
                message (topic, payload) to publish
        """
        payload = json.dumps(lastwill_msg.payload)
        logger.debug(f"Setting last will \
                            {str(lastwill_msg.topic)}: {payload}")
        self.will_set(lastwill_msg.topic, payload)

    def message_handler_add(self,
                                topic: str,
                                handler: Callable[[PubsubMessage], None],
                                include_subtopics: bool=False
                                ) -> None:
        """
            Subscribes to topic and adds a message handler for messages received;
            Called by PubsubHandler
            topic:
                the topic to subscribe
            handler:
                the handler callback to be used. received a PubsubMessage.
        """
        subs_topic = topic
        if include_subtopics:
            if not topic.endswith('#'):
                if not topic.endswith('/'):
                    subs_topic += '/'
                subs_topic += '#'
        (result, mid) = self.subscribe(subs_topic)
        if result == paho.MQTT_ERR_SUCCESS:
            self.__subscribe_mid[mid] = subs_topic
        self.__topic_dispatcher[topic] = handler

    def message_handler_remove(self, topic: str) -> None:
        """unsubscribes to topic and removes message handler
            topic:
                the topic to subscribe
        """
        found_mid = None
        for mid in self.__subscribe_mid:
            if self.__subscribe_mid[mid].startswith(topic):
                found_mid = mid
                break
        if found_mid:
            subs_topic = self.__subscribe_mid.pop(found_mid, None)
            self.unsubscribe(subs_topic)
        else: self.unsubscribe(topic)
        self.__topic_dispatcher.pop(topic, None)

    def message_publish(self, pubsub_msg: PubsubMessage) -> None:
        """Publish a message; Called by PubsubHandler
            pubsub_msg : PubsubMessage
                message (topic, payload) to publish
        """
        payload = json.dumps(pubsub_msg.payload)
        logger.debug(f"Publish msg: {str(pubsub_msg.topic)}: {payload}")
        self.publish(pubsub_msg.topic, payload)

    def __json_decode(self, msg: PubsubMessage) -> PubsubMessage:
        """Decode JSON MQTT message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if payload[0] == "'":
            payload = payload[1:len(payload) - 1]
        return PubsubMessage(msg.topic, json.loads(payload))

    def __on_message(self, msg: PubsubMessage) -> PubsubMessage:
        """Message handler internals.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```RuntimeException``` which should be given as a response.
        """

        try:
            decoded_mqtt_msg = self.__json_decode(msg)
        except JSONDecodeError:
            return PubsubMessage(self._error_topic,
                {"desc": "Invalid JSON", "data": msg.payload})

        handler = self.__topic_dispatcher.get(decoded_mqtt_msg.topic)

        if callable(handler):
            try:
                # check if method is bound
                if hasattr(handler, '__self__'):
                    return handler(decoded_mqtt_msg)
                else:
                    return handler(self._th, decoded_mqtt_msg)
            # Runtime Exceptions are raised by handlers in response to
            # invalid request data (which has been detected).
            except RuntimeException as runtime_ex:
                return runtime_ex.message
            # Uncaught exceptions should only be due to programmer error.
            except Exception as e:
                logger.warning(traceback.format_exc())
                logger.warning(f"Input message: {str(decoded_mqtt_msg.payload)}")
                return PubsubMessage(self._error_topic,
                    {"desc": "Uncaught exception", "data": str(e)})
        else:
            return PubsubMessage(self._error_topic, {"desc": "Invalid topic", "data": msg.topic})