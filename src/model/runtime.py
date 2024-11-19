"""
*TL;DR
Runtime model; Store information about the runtime
"""

import uuid

from .model_base import ModelBase
from .runtime_types import *
from .runtime_topics import RuntimeTopics
from .sl_msgs import SlMsgs
from pubsub import PubsubMessage
class Runtime(ModelBase, dict):
    """A dictionary to hold runtime properties"""

    # required attributes
    _required_attrs = ['uuid', 'name', 'runtime_type', 'max_nmodules', 'apis']

    # if True, only accepts declared attributes at init
    _strict = True

    # attributes we send in register/unregister requests
    __reg_attrs = ['uuid', 'type', 'name', 'runtime_type', 'max_nmodules', 'apis', 'is_orchestration_runtime', 'tags']
    
    # attributes we send in keepalives
    __ka_attrs = ['uuid', 'type', 'name', 'runtime_type', 'max_nmodules', 'apis', 'is_orchestration_runtime', 'tags']
    
    def __init__(self, topics: RuntimeTopics, uuid: str=str(uuid.uuid4()), attr_replace: dict=None, **kwargs):
        """Intanciate a Runtime  
        Parameters
        ----------
            topics: RuntimeTopics object
            uuid: runtime uuid
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """
        self.__rt_msgs = SlMsgs(uuid)
        self.__topics = RuntimeTopics(**topics)
        
        # replace attributes in arguments received
        if attr_replace: 
            self._replace_attrs(kwargs, attr_replace)
        
        # transform api string into an array
        if isinstance(kwargs.get('apis'), str):
            kwargs['apis'] = kwargs.get('apis').split(' ')

        kwargs['uuid'] = uuid
        kwargs['type'] = MessageType.rt
        
        # check if we have all required properties
        self._check_attrs(Runtime, kwargs)
        
        dict.__init__(self, kwargs)

    @property
    def uuid(self):
        return self['uuid']

    @uuid.setter
    def uuid(self, rt_uuid):
        self['uuid'] = str(rt_uuid)

    @property
    def name(self):
        return self['name']

    @name.setter
    def name(self, rt_name):
        self['name'] = rt_name

    @property
    def namespace(self):
        return self['namespace']

    @name.setter
    def namespace(self, rt_ns):
        self['namespace'] = rt_ns

    @property
    def type(self):
        return self['type']

    @type.setter
    def type(self, rt_type):
        self['type'] = rt_type
        
    @property
    def runtime_type(self):
        return self['runtime_type']

    @runtime_type.setter
    def runtime_type(self, rt_type):
        self['runtime_type'] = rt_type

    @property
    def max_nmodules(self):
        return self['max_nmodules']

    @max_nmodules.setter
    def max_nmodules(self, rt_max_nmodules):
        self['max_nmodules'] = rt_max_nmodules

    @property
    def reg_attempts(self):
        return self['reg_attempts']

    @reg_attempts.setter
    def reg_attempts(self, rt_reg_attempts):
        self['reg_attempts'] = rt_reg_attempts

    @property
    def reg_timeout_seconds(self):
        return self['reg_timeout_seconds']

    @reg_timeout_seconds.setter
    def reg_timeout_seconds(self, rt_reg_timeout_seconds):
        self['reg_timeout_seconds'] = rt_reg_timeout_seconds

    @property
    def reg_fail_error(self):
        return self['reg_fail_error']

    @reg_fail_error.setter
    def reg_fail_error(self, rt_reg_fail_error):
        self['reg_fail_error'] = rt_reg_fail_error

    @property
    def ka_interval_sec(self):
        return self['ka_interval_sec']

    @ka_interval_sec.setter
    def ka_interval_sec(self, rt_ka_interval_sec):
        self['ka_interval_sec'] = rt_ka_interval_sec

    @property
    def realm(self):
        return self['realm']

    @realm.setter
    def realm(self, rt_realm):
        self['realm'] = rt_realm

    @property
    def apis(self):
        return self['apis']

    @apis.setter
    def apis(self, rt_apis):
        self['apis'] = rt_apis

    @property
    def dft_scene(self):
        return self['dft_scene']

    @dft_scene.setter
    def dft_scene(self, rt_dft_scene):
        self['dft_scene'] = rt_dft_scene

    @property
    def is_orchestration_runtime(self):
        return self['is_orchestration_runtime']

    @is_orchestration_runtime.setter
    def is_orchestration_runtime(self, rt_is_orchestration_runtime):
        self['is_orchestration_runtime'] = rt_is_orchestration_runtime

    @property
    def tags(self):
        return self['tags']

    @tags.setter
    def tags(self, rt_tags):
        self['tags'] = rt_tags

    @property
    def topics(self):
        return self.__topics
    
    def _create_delete_runtime_msg(self, action) -> PubsubMessage:
        """Create/Delete (according to action) runtime message.
        Parameters
        ----------
            action (RuntimeTypes.Action): message action (create=register/delete=unregister)
        """
        # return a view of the object for a register/unregister request
        reg_req = dict(map(lambda k: (k, self.get(k)), self.__reg_attrs))
        return self.__rt_msgs.req(self.__topics.runtimes, action, reg_req)
            
    def create_runtime_msg(self) -> PubsubMessage:
        return self._create_delete_runtime_msg(Action.create)

    def delete_runtime_msg(self) -> PubsubMessage:
        return self._create_delete_runtime_msg(Action.delete)

    def keepalive_msg(self, children) -> PubsubMessage:
        keepalive = dict(map(lambda k: (k, self.get(k)), self.__ka_attrs))
        # add children
        keepalive['children'] = children
        return self.__rt_msgs.req(self.__topics.keepalive, Action.update, keepalive)
        
        pass
