"""
*TL;DR
Interaction between launcher and client classes
"""

from typing import Protocol
from abc import abstractmethod

class Launcher(Protocol):
    """Launcher receives requests to start/stop modules"""

    @abstractmethod
    def module_start(self, module):
        """Start a module"""
        raise NotImplementedError
