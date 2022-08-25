""" Create runtime messages from internal data structures with runtime/module/... info
    Translate between internal data structures and messages
"""
import uuid
import json

from pubsub.pubsub_msg import PubsubMessage
from common import MissingField
from model import Action, Result

class RuntimeMsgs:

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
        
    def __init__(self, topics, attr_replace={}):
        """Intanciate runtime messages.  Translate between internal runtime data and messages
        
        Parameters
        ----------
            topics (dict): topics where to publish
            attr_replace (dict): dictionary of attributes replaced in the runtime/module attributes
                e.g. attr_replace = { "id": "uuid"} => means that "id" in runtime/module attributes will be replaced by "uuid" in messages
        """
        self.topics = topics
        # try to automatically support old topic names
        if not hasattr(self.topics, 'runtimes'):
            setattr(self.topics, 'runtime', self.topics.reg)
        if not hasattr(self.topics, 'modules'):
            setattr(self.topics, 'modules', self.topics.ctl)
        self.attr_replace = attr_replace
        
    def error(self, data):
        """Error message to stderr topic."""
        return PubsubMessage(self.topics.stderr, data)

    def resp(self, topic, src_uuid, details, result=Result.ok, convert=False):
        """Response base message."""
        if convert:
            self.__convert_str_attrs(details)
        return PubsubMessage(topic, {
            "object_id": str(src_uuid), "type": "runtime_resp",
            "data": {"result": result, "details": details}
        })

    def req(self, topic, action, data, convert=True):
        """Request base message."""
        if convert:
            self.__convert_str_attrs(data)
        return PubsubMessage(topic, {
            "object_id": str(uuid.uuid4()), "action": action, "type": "runtime_req",
            "data": data
        })
                
    def create_delete_runtime(self, rt_data, action):
        """Create/Delete (according to action) runtime message.
        Parameters
        ----------
            action (RuntimeTypes.Action): message action (create=register/delete=unregister)
        """
        reg_req = self.__prepare_msg_attrs(rt_data, self.attr_replace) 
        return self.req(self.topics.runtimes, action, reg_req)
            
    def create_runtime(self, rt_data):
        return self.create_delete_runtime(rt_data, Action.create)

    def delete_runtime(self, rt_data):
        return self.create_delete_runtime(rt_data, Action.delete)

    def confirm_module(self, src_msg, result=Result.ok):
        return self.resp(self.topics.modules, src_msg.payload['object_id'], src_msg.payload['data'], result)
