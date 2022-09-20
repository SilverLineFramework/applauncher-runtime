"""
*TL;DR
Module model; Store information about wasm modules running
"""

from uuid import uuid4

from .model_base import ModelBase
from .runtime_types import *
from .sl_msgs import SlMsgs

class Module(ModelBase, dict):
    """A dictionary to hold module properties"""

    # required attributes
    _required_attrs = ['uuid', 'name', 'filename', 'filetype']
    
    # if True, only accepts declared attributes at init
    _strict = True

    # attributes we return for keepalive
    _ka_attrs = ['uuid', 'name']

    def __init__(self, io_base_topic='realm/proc/io/rt_uuid', uuid=str(uuid4()), attr_replace=None, **kwargs):
        """Intanciate a Module  
        Parameters
        ----------
            io_base_topic: Base topic where modules publish io. e.g.: realm/proc/io/rt_uuid
            uuid: runtime uuid        
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """        
        self.__topics =  {
            'stdout': f"{io_base_topic}/{uuid}/stdout",
            'stdin': f"{io_base_topic}/{uuid}/stdin",
            'stderr': f"{io_base_topic}/{uuid}/stderr",
        }

        kwargs['uuid'] = uuid
        kwargs['type'] = MessageType.mod
                
        # replace attributes in arguments received
        if attr_replace: 
            self._replace_attrs(kwargs, attr_replace)
        
        # check if we have all required properties
        self._check_attrs(Module, kwargs)

        dict.__init__(self, kwargs)

    @property
    def uuid(self):
        return self['uuid']

    @uuid.setter
    def uuid(self, uuid):
        self['uuid'] = str(uuid)

    @property
    def name(self):
        return self['name']

    @name.setter
    def name(self, mod_name):
        self['name'] = mod_name

    @property
    def type(self):
        return self['type']

    @type.setter
    def type(self, mod_type):
        self['type'] = mod_type

    @property
    def parent(self):
        return self.get('parent')

    @parent.setter
    def parent(self, parent_rt):
        self['parent'] = parent_rt

    @property
    def filename(self):
        return self.get('filename')

    @filename.setter
    def filename(self, fn):
        self['filename'] = fn

    @property
    def filetype(self):
        return self.get('filetype')

    @filetype.setter
    def filetype(self, ft):
        self['filetype'] = ft

    @property
    def fileid(self):
        return self.get('fileid')

    @fileid.setter
    def fileid(self, fid):
        self['fileid'] = fid

    # apis list of strings
    @property
    def apis(self):
        return self.get('apis', [])

    @apis.setter
    def apis(self, m_apis):
        self['apis'] = m_apis
        
    # command arguments as a string or list of strings
    @property
    def args(self):
        return self.get('args', [])

    @args.setter
    def args(self, m_args):
        self['args'] = m_args

    # environment variables as a dictionary or a list of strings in the format ["SOMEVARIABLE=xxx"].
    @property
    def env(self):
        return self.get('env', [])

    @env.setter
    def env(self, m_env):
        self['env'] = m_env 

    # channels as a list of chanel objects
    @property
    def channels(self):
        return self.get('channels', [])

    @channels.setter
    def channels(self, m_channels):
        self['channels'] = m_channels

    # peripherals as a list of peripherals objects
    @property
    def peripherals(self):
        return self.get('peripherals', [])

    @peripherals.setter
    def peripherals(self, m_peripherals):
        self['peripherals'] = m_peripherals
        
    # resources as a list of resources objects
    @property
    def resources(self):
        return self.get('resources', [])

    @resources.setter
    def resources(self, m_resources):
        self['resources'] = m_resources

    @property
    def fault_crash(self):
        return self.get('fault_crash', [])

    @fault_crash.setter
    def fault_crash(self, m_fault_crash):
        self['fault_crash'] = m_fault_crash
        
    @property
    def status(self):
        return self.get('status')

    @status.setter
    def status(self, m_status):
        self['fault_crash'] = m_status

    @property
    def topics(self):
        return self.__topics
    
    def keepalive_attrs(self, mod_stats):
        keepalive = dict(map(lambda k: (k, self.get(k)), self._ka_attrs))
        return { **keepalive, **mod_stats }
        
