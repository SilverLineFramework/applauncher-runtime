"""MQTT Message definitions."""

class MQTTMessage:
    """MQTT Message container."""

    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload

    def get(self, *args):
        """Get attribute, or raise appropriate error.

        Raises
        ------
        MissingField
            Equivalent of ```KeyError```, with appropriate error generation.
        """
        try:
            d = self.payload
            for p in args:
                d = d[p]
            return d
        except (KeyError, TypeError):
            raise MissingField(args)
