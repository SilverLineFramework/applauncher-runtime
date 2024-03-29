
from .model_base import ModelBase

class ModuleStats(ModelBase, dict):
    """A dictionary to hold module stats"""

    # required attributes
    _required_attrs = ['cpu_usage_percent']
    
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
    def cpu_usage_percent(self):
        return self['cpu_usage_percent']

    @cpu_usage_percent.setter
    def cpu_usage_percent(self, cpu_usage_percent):
        # cpu percent must be positive
        if cpu_usage_percent >= 0: self['cpu_usage_percent'] = cpu_usage_percent

    @property
    def mem_usage(self):
        return self['mem_usage']

    @mem_usage.setter
    def mem_usage(self, mem_usage):
        # mem_usage must be positive
        if mem_usage >= 0: self['mem_usage'] = mem_usage

    @property
    def network_rx_mb(self):        
        return self['network_rx_mb']

    @network_rx_mb.setter
    def network_rx_mb(self, network_rx_mb):
        # network rx must be positive
        if network_rx_mb >= 0: self['network_rx_mb'] = network_rx_mb

    @property
    def network_tx_mb(self):
        return self['network_tx_mb']

    @network_tx_mb.setter
    def network_tx_mb(self, network_tx_mb):
        # network tx must be positive
        if network_tx_mb >= 0: self['network_tx_mb'] = network_tx_mb
        
    @property
    def network_tx_pkts(self):
        return self['network_tx_pkts']

    @network_tx_pkts.setter
    def network_tx_pkts(self, network_tx_pkts):
        # network tx pkts must be positive
        if network_tx_pkts >= 0: self['network_tx_pkts'] = network_tx_pkts        

    @property
    def network_rx_pkts(self):
        return self['network_rx_pkts']

    @network_rx_pkts.setter
    def network_rx_pkts(self, network_rx_pkts):
        # network tx pkts must be positive
        if network_rx_pkts >= 0: self['network_rx_pkts'] = network_rx_pkts
