"""MQTT Message definitions."""
from typing import Dict

from common import MissingField

class PubsubMessage(dict):
    """Pubsub Message container."""

    def __init__(self, topic: str, payload: Dict):
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
        except (KeyError, TypeError) as key_exc:
            raise MissingField(p) from key_exc

    def __repr__(self) -> str:
        return f"{self.topic}: {self.payload}"