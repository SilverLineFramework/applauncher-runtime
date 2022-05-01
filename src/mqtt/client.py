"""MQTT Client."""

import traceback
import json
import paho.mqtt.client as paho
import uuid
import ssl as ssl_lib
from json.decoder import JSONDecodeError
from logzero import logger

from common.config import settings
from common.messages import ErrorMsg
from common.exception import RuntimeException

from .mqtt_msg import MQTTMessage
from .interface import PubsubClient

class MQTTClient(paho.Client, PubsubClient):
    """MQTT client class extending mqtt.Client. Implements PubsubClient methods.

    Parameters
    ----------
    topic_handler: PubsubHandler
        send notifications (connected, error, topic messages) to topic_handler
    host: str
        MQTT host
    port: int
        MQTT port
    username: str
        MQTT user
    password: str
        MQTT password
    ssl: boolean
        MQTT ssl connection
    cid : str
        Client ID for paho MQTT client.
    """

    __topic_dispatcher = {}
    __subscribe_mid = {}

    def __init__(self, topic_handler, host='arenaxr.org', port=1883, username=None, password=None, ssl=False, cid=uuid.uuid4()):
        super().__init__(str(cid))

        logger.debug("[MQTTClient.Init] Starting MQTT client...")

        self.th = topic_handler;

        self.__connect_and_subscribe(host, port, username, password, ssl)

    def __connect_and_subscribe(self, host, port, username, password, ssl):
        """Subscribe to control topics."""
        if username and password:
            self.username_pw_set(username=username, password=password)
        if ssl:
            self.tls_set(cert_reqs=ssl_lib.CERT_NONE)

        self.connect(host, port, 60)

        self.loop_start()

    def on_connect(self, mqttc, userctx, flags, rc):
        """Client connect callback."""
        if rc == 0:
            logger.debug("[MQTTClient.Connect] Connected.")
            self.th.pubsub_connected(mqttc)
        else:
            logger.error(f"[MQTTClient.Connect] Bad connection returned code={rc}")

    def on_message(self, mqttc, userctx, msg):
        """MQTT Message handler."""

        res = self.__on_message(msg)
        # only publish if not `None`
        if res:
            payload = json.dumps(res.payload)
            print("[Response] {}: {}".format(str(res.topic), payload))
            self.publish(res.topic, payload)

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """Subscribe callback."""
        logger.debug("[MQTTClient.Subscribe] Subscribed: {}".format(self.__subscribe_mid.get(mid, 'to a topic.')))

    def on_log(self, mqttc, obj, level, string):
        """Logging callback."""

        if (level == paho.MQTT_LOG_ER):
            logger.error(f"[MQTTClient.Log] MQTT Error: {string}")
            self.th.pubsub_error("[MQTTClient.Log] MQTT Error", string)
            return
        elif (level == paho.MQTT_LOG_WARNING): logger.warning(string)
        elif (level == paho.MQTT_LOG_INFO): logger.info(string)
        else: logger.debug(string)

    def pubsub_last_will_set(self, lastwill_msg):
        """Set last will message; If the client disconnects without calling disconnect(),
           the broker will publish the message on its behalf.
            lastwill_msg : PubsubMessage
                message (topic, payload) to publish
        """
        payload = json.dumps(lastwill_msg.payload)
        logger.debug("[MQTTClient.LastWill] Setting last will {}: {}".format(str(lastwill_msg.topic), payload))
        self.will_set(lastwill_msg.topic, payload)

    def pubsub_message_handler_add(self, topic, handler, include_subtopics=False):
        """Subscribes to topic and adds a message handler for messages received; Called by PubsubHandler
            topic:
                the topic to subscribe
            handler:
                the handler callback to be used. received a PubsubMessage.
        """
        subs_topic = topic
        if include_subtopics:
            if not topic.endswith('#'):
                if not topic.endswith('/'): subs_topic += '/'
                subs_topic += '#'
        (result, mid) = self.subscribe(subs_topic)
        if result == paho.MQTT_ERR_SUCCESS: self.__subscribe_mid[mid] = subs_topic
        self.__topic_dispatcher[topic] = handler;

    def pubsub_message_handler_remove(self, topic):
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

    def pubsub_message_publish(self, pubsub_msg):
        """Publish a message; Called by PubsubHandler
            pubsub_msg : PubsubMessage
                message (topic, payload) to publish
        """
        payload = json.dumps(pubsub_msg.payload)
        logger.debug("[MQTTClient.MsgPublish] {}: {}".format(str(pubsub_msg.topic), payload))
        self.publish(pubsub_msg.topic, payload)

    def __json_decode(self, msg):
        """Decode JSON MQTT message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if (payload[0] == "'"):
            payload = payload[1:len(payload) - 1]
        return MQTTMessage(msg.topic, json.loads(payload))

    def __on_message(self, msg):
        """Message handler internals.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```RuntimeException``` which should be given as a response.
        """

        try:
            decoded_mqtt_msg = self.__json_decode(msg)
        except JSONDecodeError:
            return ErrorMsg(
                {"desc": "Invalid JSON", "data": msg.payload})

        handler = self.__topic_dispatcher.get(decoded_mqtt_msg.topic)

        if callable(handler):
            try:
                return handler(decoded_mqtt_msg)
            # Runtime Exceptions are raised by handlers in response to
            # invalid request data (which has been detected).
            except RuntimeException as e:
                return e.message
            # Uncaught exceptions should only be due to programmer error.
            except Exception as e:
                logger.warning(traceback.format_exc())
                logger.warning("Input message: {}".format(str(decoded_mqtt_msg.payload)))
                return ErrorMsg(
                    {"desc": "Uncaught exception", "data": str(e)})
        else:
            return ErrorMsg({"desc": "Invalid topic", "data": msg.topic})
