
from .model_base import ModelBase

class RuntimeTopics(ModelBase, dict):
    """A dictionary to hold runtime topics"""

    # required attributes
    _required_attrs = ['modules', 'runtimes', 'mio']
    
    # if True, only accepts declared attributes at init
    _strict = False
    
    def __init__(self, attr_replace=None, **config_args):        
        """Intanciate RuntimeTopics  
        Parameters
        ----------
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            config_args: topics from config to be added as attributes
        """
        
        # replace attributes in arguments received
        if attr_replace: 
            self._replace_attrs(config_args, attr_replace)
                
        # check if we have all required properties
        self._check_attrs(RuntimeTopics, config_args)

        dict.__init__(self, config_args)

    @property
    def modules(self):
        return self['modules']

    @modules.setter
    def modules(self, modules):
        self['modules'] = modules

    @property
    def runtimes(self):
        return self['runtimes']

    @runtimes.setter
    def runtimes(self, runtimes):
        self['runtimes'] = runtimes
        
    # convenience property; =runtimes
    @property
    def keepalive(self):
        return self['runtimes']

    # convenience property; =runtimes
    @property
    def error(self):
        return self['runtimes']

    # module io will have module_uuid, namespaced_scene (passed as argument) replaced during runtime 
    @property
    def mio(self, **kwargs):
        return self['mio'].format(kwargs)

    @mio.setter
    def mio(self, io, **kwargs):
        self['mio'] = io.format(kwargs)

    