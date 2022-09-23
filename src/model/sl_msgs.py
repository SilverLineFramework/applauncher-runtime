""" Create silverline messages from internal data structures with runtime/module/... info
    Translate between internal data structures and messages
"""
import uuid
import json

from pubsub.pubsub_msg import PubsubMessage
from common import MissingField
from model.runtime_types import Result, MessageType

class SlMsgs:

    def __convert_str_attrs(self, d):
        """Convert JSON-encoded string attributes into proper objects."""
        convert_keys = ['apis', 'args', 'env', 'channels', 'peripherals', 'aot_target']
        # convert array attributes saved as strings into objects
        for key in convert_keys:
            try:
                attr_str = d[key].replace("'", '"')
                d[key] = json.loads(attr_str)
            except Exception as _:
                pass
    
    def __prepare_msg_attrs(self, data, attr_replace={}):
        """Replaces attributes given in attr_replace  
        Parameters
        ----------
            data (dict): source message data
            attr_replace (dict): dictionary of attributes to replace in data
                e.g. attr_replace = { "id": "uuid"} => means that "id" in data will be replaced by "uuid"
        """
        try: 
            d = dict(data.copy())
            for key in attr_replace:
                d[attr_replace[key]] = d.pop(key)
        except (KeyError, TypeError) as key_exc:
            raise MissingField(d) from key_exc
        
        return d
        
    def __init__(self, attr_replace={}):
        """Intanciate runtime messages. Translate between internal runtime data and messages
        
        Parameters
        ----------
            attr_replace (dict): dictionary of attributes replaced in the runtime/module attributes
                e.g. attr_replace = { "id": "uuid"} => means that "id" in runtime/module attributes will be replaced by "uuid" in messages
        """
        self.attr_replace = attr_replace
        
    def error(self, data):
        """Error message to stderr topic."""
        return PubsubMessage(self.topics.stderr, data)

    def resp(self, topic, src_uuid, action, details, result=Result.ok, convert=False) -> PubsubMessage:
        """Response base message."""
        if convert:
            self.__convert_str_attrs(details)
        return PubsubMessage(topic, {
            "object_id": str(src_uuid), "action": action, "type": MessageType.rt_response,
            "data": {"result": result, "details": details}
        })

    def req(self, topic, action, req, convert=True) -> PubsubMessage:
        """Request base message."""
        data = self.__prepare_msg_attrs(req, self.attr_replace) 
        
        if convert:
            self.__convert_str_attrs(data)

        return PubsubMessage(topic, {
            "object_id": str(uuid.uuid4()), "action": action, "type": MessageType.rt_request,
            "data": data
        })
    