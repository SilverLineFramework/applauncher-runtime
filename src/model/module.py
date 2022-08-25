"""
*TL;DR
Module model; Store information about wasm modules running
"""

import uuid

from common import MissingField
from .runtime_types import *

class Module(dict):
    """A dictionary to hold module properties"""

    __required_props = ['name', 'filename', 'filetype']

    def __init__(self, uuid=str(uuid.uuid4()), **kwargs):

        # check if we have all required properties
        for k in self.__required_props:
            if not k in kwargs:
                raise MissingField(f"Module property {k} not in {str(kwargs)}")

        kwargs['uuid'] = uuid
        kwargs['type'] = MessageType.mod
        
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
    def parent(self):
        return self['parent']

    @parent.setter
    def parent(self, parent_rt):
        self['parent'] = parent_rt

    @property
    def filename(self):
        return self['filename']

    @filename.setter
    def filename(self, fn):
        self['filename'] = fn

    @property
    def filetype(self):
        return self['filetype']

    @filetype.setter
    def filetype(self, ft):
        self['filetype'] = ft

    @property
    def fileid(self):
        return self['fileid']

    @fileid.setter
    def fileid(self, fid):
        self['fileid'] = fid

    @property
    def args(self):
        return self['args']

    @args.setter
    def args(self, m_args):
        self['args'] = m_args

    @property
    def env(self):
        return self['env']

    @env.setter
    def env(self, m_env):
        self['env'] = m_env
