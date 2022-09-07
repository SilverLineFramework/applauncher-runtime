"""
*TL;DR
Module model; Store information about wasm modules running
"""

import uuid

from .runtime_model import RuntimeModel
from .runtime_types import *

class Module(RuntimeModel, dict):
    """A dictionary to hold module properties"""

    # required attributes
    _required_attrs = ['uuid', 'type', 'name', 'filename', 'filetype']
    
    # if True, only accepts declared attributes at init
    _strict = True

    def __init__(self, uuid=str(uuid.uuid4()), attr_replace=None, **kwargs):
        """Intanciate a Module  
        Parameters
        ----------
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """
        
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
    def uuid(self, mod_uuid):
        self['uuid'] = str(mod_uuid)

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
        return self.get('parent', None)

    @parent.setter
    def parent(self, parent_rt):
        self['parent'] = parent_rt

    @property
    def filename(self):
        return self.get('filename', None)

    @filename.setter
    def filename(self, fn):
        self['filename'] = fn

    @property
    def filetype(self):
        return self.get('filetype', None)

    @filetype.setter
    def filetype(self, ft):
        self['filetype'] = ft

    @property
    def fileid(self):
        return self.get('fileid', None)

    @fileid.setter
    def fileid(self, fid):
        self['fileid'] = fid

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

    def topics(self, modules_io_base_topic='real/proc/stdio/rt_uuid'):
        return {
            'stdout': f"{modules_io_base_topic}/{self.uuid}/stdout",
            'stdin': f"{modules_io_base_topic}/{self.uuid}/stdin",
            'stderr': f"{modules_io_base_topic}/{self.uuid}/stderr",
        }