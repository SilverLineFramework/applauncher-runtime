"""
*TL;DR
Base class for runtime models;
"""

from typing import Dict
from common import MissingField, NotDeclaredField
from typing import Protocol
from abc import abstractmethod

class ModelBase(Protocol):
    """ 
        Base class for runtime models; 
        Checks arguments used as attributes for a derived model class and utility call to replace arguments
    """

    @property
    @abstractmethod
    def _required_attrs(self):
        pass

    @property
    @abstractmethod
    def _strict(self):
        pass

    def _check_attrs(self, of_class, kwargs):
        """ Check if arguments have required attributes and only declared attributes are present (if strict=True) """

        # check if we have all required properties
        for k in of_class._required_attrs:
            if not k in kwargs:
                raise MissingField(f"Module property {k} not in {str(kwargs)}")
        if of_class._strict:
            # check all properties provided are part of the declared properties
            class_properties = [p for p in dir(of_class) if isinstance(getattr(of_class,p),property)]
            for key in kwargs:
                if not key in class_properties:
                    err_str = "Property {} is not declared as a valid attribute of {}".format(key, of_class.__name__)
                    raise NotDeclaredField(err_str)
    
    def _replace_attrs(self, data, attr_replace={}) -> Dict:
        """Replaces attributes given in attr_replace  
        Parameters
        ----------
            data (dict): source dictionary
            attr_replace (dict): dictionary of attributes to replace in data
                e.g. attr_replace = { "id": "uuid"} => means that "id" in data will be replaced by "uuid"
        """
        try: 
            d = dict(data.copy())
            for key in attr_replace:
                d[attr_replace[key]] = d.pop(key)
        except (KeyError, TypeError) as key_exc:
            raise MissingField(d) from key_exc
        
        return d