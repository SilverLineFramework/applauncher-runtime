"""
*TL;DR
Runtime model; Store information about the runtime
"""

import uuid

from .runtime_model import RuntimeModel
from .runtime_types import *

class Runtime(RuntimeModel, dict):
    """A dictionary to hold runtime properties"""

    # required attributes
    _required_attrs = ['uuid', 'type', 'name', 'runtime_type', 'max_nmodules', 'apis']

    # if True, only accepts declared attributes at init
    _strict = True
    
    def __init__(self, uuid=str(uuid.uuid4()), attr_replace=None, **kwargs):
        """Intanciate a Runtime  
        Parameters
        ----------
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """
        
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
    def apis(self):
        return self['apis']

    @apis.setter
    def apis(self, rt_apis):
        self['apis'] = rt_apis

    def _register_unregister_req(self, action):
        reg_keys = ['uuid', 'name', 'apis', 'max_nmodules', 'runtime_type']
        reg_req = dict(map(lambda k: (k, str(self.get(k))), reg_keys))
        req = RequestMsg(self.reg_topic, action, reg_req)
        return req

    def register_req(self):
        return self._register_unregister_req(Action.create)

    def unregister_req(self):
        return self._register_unregister_req(Action.delete)
