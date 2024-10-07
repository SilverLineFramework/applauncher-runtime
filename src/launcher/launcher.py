"""
*TL;DR
Interface a module launcher must expose; 
Module launchers implement the details to start a module in different ways;
For example, a module launcher can start python programs inside a container and instanciate
a docker client to do so (this is what PythonLauncher does). Other launchers can be implemented.
A module launcher factory (LauncherContext) instanciates launchers based on settings
"""

from typing import Protocol, Dict, Callable
from abc import abstractmethod
from enum import Enum
from logzero import logger
from dynaconf import LazySettings

from model import Module, ModuleStats
from common import settings, LauncherException, ClassUtils
from program_files import ProgramFilesBuilder
from pubsub import PubsubListner

class ModuleLauncher(Protocol):
    """
        Launcher receives requests to start/stop a module
        A launcher prepares the program files and environment (container, ...) to run the program
    """

    @abstractmethod
    def start_module(self, exit_notify: Callable=None, pubsubc: PubsubListner = None, topics: Dict = None):
        """Start module; Optionally provide an exit notify callable and setup a streamer for stdin, stdout, stderr"""
        raise NotImplementedError

    @abstractmethod
    def stop_module(self):
        """Stop module"""
        raise NotImplementedError

    @abstractmethod
    def get_stats(self) -> ModuleStats:
        """Return module stats"""
        raise NotImplementedError

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
    
class LauncherContext():
    """ModuleLauncher factory; Instantiate a ModuleLauncher given a module"""

    @staticmethod
    def get_launcher_for_module(module: Module, **kwargs) -> ModuleLauncher:
        """
            ModuleLauncher factory method; gets launcher based on module filetype
        """

        ls = {k:v for (k,v) in settings.launcher.items() if not isinstance(v, dict)}

        # get filetype-specific settings and merge 
        ft_ls = settings.launcher.get(module.filetype)
        if not ft_ls:
            raise LauncherException(f"No launcher configured for type {module.filetype}")
        ls = {**ls, **ft_ls}

        # create launcher instance from settings
        logger.debug(f"Importing {ls.get('class')}")
        mlauncher = ClassUtils.class_instance_from_settings_class_path(
                            f"launcher.{module.filetype}.class", launcher_settings=ls, module=module, **kwargs)
        return mlauncher

class QoSParams(Protocol):
    """
        An interface to convert a request arguments (usually a module create) into
        a system/launcher-specific config
    """

    class QosClass(Enum):
        """QoS Classes"""
        RT = 1
        BE = 2

    @abstractmethod
    def get_qos_config(self, **kwargs) -> Dict:
        """Return the config given a request parameters"""
        raise NotImplementedError