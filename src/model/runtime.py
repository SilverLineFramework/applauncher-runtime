"""
*TL;DR
Runtime model; Store information about the runtime
"""

import uuid

from common import settings, MissingField
from .runtime_types import *

class Runtime(dict):
    """A dictionary to hold runtime properties"""

    __required_props = ['name', 'runtime_type', 'max_nmodules', 'apis']

    def __init__(self, uuid=str(uuid.uuid4()), **kwargs):
        # transform api string into an array
        if isinstance(kwargs.get('apis'), str):
            kwargs['apis'] = kwargs.get('apis').split(' ')

        # check if we have all required properties
        for k in self.__required_props:
            if not k in kwargs:
                raise MissingField(f"Runtime property {k} not in {str(kwargs)}")

        kwargs['uuid'] = uuid
        kwargs['type'] = MessageType.rt
        
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
