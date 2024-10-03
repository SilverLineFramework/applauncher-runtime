"""
*TL;DR
Module model; Store information about wasm modules running
"""

from uuid import uuid4
import re 

from .model_base import ModelBase
from .runtime_types import *

DFT_NAMESPACE='public'
DFT_SCENE='default'

KEY_NS_ENV='NAMESPACE'
KEY_SCENE_ENV='SCENE'

class Module(ModelBase, dict):
    """A dictionary to hold module properties"""

    # required attributes
    _required_attrs = ['uuid', 'name', 'file', 'filetype']
    
    # if True, only accepts declared attributes at init
    _strict = False

    # attributes we return for keepalive
    _ka_attrs = ['uuid', 'name', 'file', 'filetype', 'parent']

    # attributes we return for delete requests
    _delete_attrs = ['type', 'uuid', 'name', 'parent']

    def __init__(self, mio_topic=None, uuid=str(uuid4()), attr_replace=None, **kwargs):
        """Intanciate a Module  
        Parameters
        ----------
            mio_topic: Base topic where modules publish/subscribe their stdout, stderr, stdin streams
                 should have '{namespaced_scene}' to be replaced
            uuid: runtime uuid        
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """        

        # scene attribute should be a namespaced scene
        namespaced_scene = self.__namespaced_scene(
            namespaced_scene=kwargs.get('scene'), 
            kwargs.get('env'))

        kwargs['uuid'] = uuid
        kwargs['type'] = MessageType.mod
        kwargs['scene'] = namespaced_scene
        
        # define module topics
        if mio_topic=None:
            raise InvalidArgument("mio_topic", "Module IO topic is required")

        # we need to replace the namespaced_scene
        mio_topic = mio_topic.format(namespaced_scene=namespaced_scene)
        self.__topics =  {
            'mio': mio_topic,
            'stdout': f"{mio_topic}/stdout",
            'stdin': f"{mio_topic}/stdin",
            'stderr': f"{mio_topic}/stderr",
        }

        # replace attributes in arguments received
        if attr_replace: 
            self._replace_attrs(kwargs, attr_replace)
        
        # check if we have all required properties
        self._check_attrs(Module, kwargs)

        dict.__init__(self, kwargs)

    def __namespaced_scene(namespaced_scene=None, env=None):
         """
            Attempts to define a namespaced scene from module request attributes:
               - 'scene': if exists and is in the form 'namespace/scene'; if not in valid format, returns default_ns/scene
               - 'env': if 'scene' is not present, searchs for namespace and scene in env parameters
         """
        if namespaced_scene:
            valid_scene = re.search("[a-z0-9_-]{3,}\/[a-z0-9_-]{3,}", namespaced_scene, re.IGNORECASE)
            namespaced_scene = f"{DFT_NAMESPACE}/{namespaced_scene}"
            return namespaced_scene

        if namespaced_scene == None or valid_scene==None:
            scene = DFT_SCENE
            namespace = DFT_NAMESPACE
            if env != None:
                if isinstance(env, dict):
                    # {'NAMESPACE': 'anamespace', 'SCENE': 'ascene'}
                    scene = env.get(KEY_SCENE_ENV, scene)
                    namespace = env.get(KEY_NS_ENV, namespace)
                elif isinstance(env, list):
                    # ['NAMESPACE=anamespace', 'SCENE=ascene']
                    for evar_str in env:
                        evar_splitted = evar_str.split('=')
                        if len(evar_splitted) == 2: 
                            if (evar_splitted[0] == KEY_SCENE_ENV): scene = evar_splitted[1]
                            if (evar_splitted[0] == KEY_NS_ENV): namespace = evar_splitted[1]
            namespaced_scene = f"{namespace}/{scene}"

        return namespaced_scene

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
    def location(self):
        return self.get('location')

    @location.setter
    def location(self, fn):
        self['location'] = fn

    @property
    def file(self):
        return self.get('file')

    @file.setter
    def file(self, fn):
        self['file'] = fn

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

    @property
    def mio(self):
        return self.__topics['mio']
    
    def keepalive_attrs(self, mod_stats):
        if mod_stats == None: return None
        keepalive = dict(map(lambda k: (k, self.get(k)), self._ka_attrs))
        return { **keepalive, **mod_stats }
        
    def delete_attrs(self):
        delete = dict(map(lambda k: (k, self.get(k)), self._delete_attrs))
        return { **delete }

    def confirm_msg(self, msg_to_confirm) -> PubsubMessage:
        return self.__rt_msgs.resp(
            self.__topics['mio'],
            msg_to_confirm.get('object_id'),
            action=msg_to_confirm.get('action'),
            details=msg_to_confirm.get('data'))
        
    def delete_msg(self) -> PubsubMessage:
        return self.__rt_msgs.req(self.__topics['mio'], 
                Action.delete, 
                self.delete_attrs())        
