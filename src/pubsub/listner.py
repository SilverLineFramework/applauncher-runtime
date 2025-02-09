"""MQTT Client."""

from subprocess import call
import traceback
import json
import ssl as ssl_lib
from json.decoder import JSONDecodeError
from typing import Dict, Tuple, Any, Callable
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

    __subscribe_mid: Dict[int, str]
    
    def __init__(self,
                pubsub_handler: PubsubHandler,
                error_topic: str = 'error_topic',
                host: str = 'arenaxr.org',
                port: int = 1883,
                username: str = None,
                password: str = None,
                ssl: bool= False,
                cid: str= str(uuid.uuid4())) -> None:

        super().__init__(paho.CallbackAPIVersion.VERSION2)

        self._error_topic = error_topic
        self.__subscribe_mid = {}

        logger.debug("Starting MQTT client...")

        self.__pubsub_handler = pubsub_handler
        if not pubsub_handler:
            logger.info("No topic handler provided! MQTT notifications will not be delivered.")

        if username and password:
            self.username_pw_set(username=username, password=password)
        if ssl:
            self.tls_set(cert_reqs=ssl_lib.CERT_NONE)

        self.connect(host, port, 60)

        self.loop_start()
        
    def __pubsub_handler_call(self, handler_call: Callable, args):
        if not self.__pubsub_handler:
            logger.info(f"Call to {getattr(callable, '__name__', repr(callable))} skipped: no pubsub handler provided.")
            
        # check if method is bound
        if hasattr(handler_call, '__self__'):
            return handler_call(args)
        else:
            return handler_call(self.__pubsub_handler, args)
    
    def on_connect(self, mqttc, userctx, flags, rc, properties) -> None:
        """Client connect callback."""
        if rc == 0:
            logger.debug("Connected.")
            self.__pubsub_handler_call(handler_call=self.__pubsub_handler.pubsub_connected, args=(mqttc))
        else:
            logger.error(f"Bad connection returned code={rc}")

    def on_message(self, mqttc, userctx, msg) -> None:
        """MQTT Message handler.
           All runtime messages are handled with callbacks on specific topics
        """

        self.message_publish(PubsubMessage(self._error_topic, {"desc": "Invalid topic", "data": msg.topic}))
        
    def on_subscribe(self, mqttc, obj, mid, reason_codes, properties) -> None:
        """Subscribe callback."""
        logger.debug(f"Subscribed: {self.__subscribe_mid.get(mid, 'to a topic.')}")
        for sub_result in reason_codes:
            # Any reason code >= 128 is a failure.
            if sub_result >= 128:
                logger.error(f"MQTT Error: Error subscribing - {sub_result}")

    def on_log(self, mqttc, obj, level, string) -> None:
        """Logging callback."""

        if level == paho.MQTT_LOG_ER:
            logger.error(f"MQTT Error: {string}")
            self.__pubsub_handler_call(handler_call=self.__pubsub_handler.pubsub_error, args=("MQTT Error", string))

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
                                decode_json: bool=True,
                                ) -> None:
        """
            Subscribes to topic and adds a message handler for messages received;
            Called by PubsubHandler
            topic:
                the topic to subscribe
            handler:
                the handler callback to be used. received a PubsubMessage.
        """
        (result, mid) = self.subscribe(topic)
        if result == paho.MQTT_ERR_SUCCESS:
             self.__subscribe_mid[mid] = topic

        callbk = lambda mqttc, userctx, msg: self.on_message_callback(msg, decode_json, handler)
        self.message_callback_add(topic, callbk)

    def message_handler_remove(self, topic: str) -> None:
        """unsubscribes to topic and removes message handler
            topic:
                the topic to subscribe
        """
        for mid in self.__subscribe_mid:
            if self.__subscribe_mid[mid] == topic:
                subs_topic = self.__subscribe_mid.pop(mid, None)
                self.unsubscribe(subs_topic)
                self.message_callback_remove(subs_topic)
                break

    def message_publish(self, pubsub_msg: PubsubMessage) -> None:
        """Publish a message; Called by PubsubHandler
            pubsub_msg : PubsubMessage
                message (topic, payload) to publish
        """

        payload = json.dumps(pubsub_msg.payload)
        logger.debug(f"Publish msg: {pubsub_msg.topic}: {payload}")
        self.publish(pubsub_msg.topic, payload)

    def __decode_msg(self, msg, decode_json: bool) -> PubsubMessage:
        """Attempt to decode JSON MQTT message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        try:
            if payload[0] == "'":
                payload = payload[1:len(payload) - 1]
        except IndexError:
            pass
        if decode_json:
            payload = json.loads(payload)
        return PubsubMessage(msg.topic, payload)

    def on_message_callback(self, msg, decode_json: bool, handler: Callable[[PubsubMessage], None]) -> None:
        """Callback message handler. 
           Perform message decoding and deliver it to handler
        """        
        res = self.__on_message_callback(msg, decode_json, handler)

        # only publish if not `None`
        if res != None:
            self.message_publish(res)
        
    def __on_message_callback(self, msg, decode_json, handler: callable) -> PubsubMessage:
        """Message callback handler internals.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```RuntimeException``` which should be given as a response.
        """        
        try:
            decoded_mqtt_msg = self.__decode_msg(msg, decode_json)
        except JSONDecodeError:
            return PubsubMessage(self._error_topic,
                {"desc": "Invalid JSON", "data": msg.payload.decode('utf-8')})

        try:
            return self.__pubsub_handler_call(handler, args = (decoded_mqtt_msg))
        except RuntimeException as rte:
            return PubsubMessage(self._error_topic, rte.error_msg_payload())
            
        # Uncaught exceptions should only be due to programmer error.
        except Exception as e:
            logger.warning(traceback.format_exc())
            logger.warning(f"Input message: {str(decoded_mqtt_msg.payload)}")
            return PubsubMessage(self._error_topic, 
                {"desc": "Uncaught exception", "data": str(e)})

