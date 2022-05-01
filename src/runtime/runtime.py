"""
*TL;DR
Runtime class; Store information about the runtime
"""


import json
import uuid

from common.config import settings
from mqtt.mqtt_msg import MQTTMessage
from common.messages import RequestMsg, Action, Type
from common.exception import MissingField

class Runtime(dict):
    """A dictionary to hold runtime properties"""
    type = Type.rt

    __required_props = ['uuid', 'name', 'runtime_type', 'max_nmodules', 'apis', 'topics']

    def __init__(self, **kwargs):
        # transform api string into an array
        kwargs['apis'] = kwargs.get('apis').split(' ')

        # check if we have all required properties
        for k in self.__required_props:
            if not k in kwargs:
                raise MissingField(f"Runtime property {k} not in {str(kwargs)}")

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

    @property
    def dbg_topic(self):
        return self['topics']['dbg']

    @dbg_topic.setter
    def dbg_topic(self, dbg_topic):
        self['topics']['dbg'] = dbg_topic

    @property
    def ctl_topic(self):
        return self['topics']['ctl']

    @ctl_topic.setter
    def ctl_topic(self, ctl_topic):
        self['topics']['ctl'] = ctl_topic

    @property
    def reg_topic(self):
        return self['topics']['reg']

    @reg_topic.setter
    def reg_topic(self, reg_topic):
        self['topics']['reg'] = reg_topic

    @property
    def stdin_topic(self):
        return self['topics']['stdin']

    @stdin_topic.setter
    def stdin_topic(self, stdin_topic):
        self['topics']['stdin'] = stdin_topic

    @property
    def stdout_topic(self):
        return self['topics']['stdout']

    @stdout_topic.setter
    def stdout_topic(self, stdout_topic):
        self['topics']['stdout'] = stdout_topic

    @property
    def stderr_topic(self):
        return self['topics']['stderr']

    @stderr_topic.setter
    def stderr_topic(self, stderr_topic):
        self['topics']['stderr'] = stderr_topic

    def _register_unregister_req(self, action):
        reg_keys = ['uuid', 'name', 'apis', 'max_nmodules', 'runtime_type']
        reg_req = dict(map(lambda k: (k, str(self.get(k))), reg_keys))
        req = RequestMsg(self.reg_topic, action, reg_req)
        return req

    def register_req(self):
        return self._register_unregister_req(Action.create)

    def unregister_req(self):
        return self._register_unregister_req(Action.delete)
