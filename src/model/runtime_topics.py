
from .model_base import ModelBase

class RuntimeTopics(ModelBase, dict):
    """A dictionary to hold runtime topics"""

    # required attributes
    _required_attrs = ['modules', 'runtimes', 'io', 'keepalive']
    
    # if True, only accepts declared attributes at init
    _strict = True
    
    def __init__(self, attr_replace=None, **kwargs):        
        """Intanciate RuntimeTopics  
        Parameters
        ----------
            attr_replace (dict): dictionary of attributes to replace in kwargs
                e.g. attr_replace = { "id": "uuid"} => means that "id" in kwargs will be replaced by "uuid"
            kwargs: arguments to be added as attributes
        """
        
        # replace attributes in arguments received
        if attr_replace: 
            self._replace_attrs(kwargs, attr_replace)
                
        # check if we have all required properties
        self._check_attrs(RuntimeTopics, kwargs)
        
        dict.__init__(self, kwargs)

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
        
    @property
    def io(self):
        return self['io']

    @io.setter
    def io(self, io):
        self['io'] = io

    @property
    def keepalive(self):
        return self['keepalive']

    @keepalive.setter
    def keepalive(self, keepalive):
        self['keepalive'] = keepalive
        
    