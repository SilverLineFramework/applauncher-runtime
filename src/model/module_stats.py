
from .model_base import ModelBase

class ModuleStats(ModelBase, dict):
    """A dictionary to hold module stats"""

    # required attributes
    _required_attrs = ['cpu_percent']
    
    # if True, only accepts declared attributes at init
    _strict = True
    
    def __init__(self, attr_replace=None, **kwargs):        
        """Intanciate ModuleStats  
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
        self._check_attrs(ModuleStats, kwargs)
        
        dict.__init__(self, kwargs)

    @property
    def cpu_percent(self):
        return self['cpu_percent']

    @cpu_percent.setter
    def cpu_percent(self, cpu_percent):
        self['cpu_percent'] = cpu_percent

    @property
    def network_rx_mb(self):
        return self['network_rx_mb']

    @network_rx_mb.setter
    def cpu_percent(self, network_rx_mb):
        self['network_rx_mb'] = network_rx_mb

    @property
    def network_tx_mb(self):
        return self['network_tx_mb']

    @network_tx_mb.setter
    def cpu_percent(self, network_tx_mb):
        self['network_tx_mb'] = network_tx_mb
        
    @property
    def network_tx_pkts(self):
        return self['network_tx_pkts']

    @network_tx_pkts.setter
    def cpu_percent(self, network_tx_pkts):
        self['network_tx_pkts'] = network_tx_pkts        

    @property
    def network_rx_pkts(self):
        return self['network_rx_pkts']

    @network_rx_pkts.setter
    def cpu_percent(self, network_rx_pkts):
        self['network_rx_pkts'] = network_rx_pkts