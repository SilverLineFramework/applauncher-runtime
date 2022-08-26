"""
*TL;DR
Interface a module launcher must expose; Define a module launcher factory
"""

from typing import Protocol, Dict
from abc import abstractmethod
from enum import Enum
from logzero import logger
from dynaconf import LazySettings

from model import Module
from common import settings, LauncherException, ClassUtils
from program_files import ProgramFilesBuilder

class ModuleLauncher(Protocol):
    """
        Launcher receives requests to start/stop a module
        A launcher prepares the program files and environment (container, ...) to run the program
    """

    _settings: LazySettings
    _module: Module
    _file_repo: ProgramFilesBuilder

    @abstractmethod
    def start_module(self):
        """Start module"""
        raise NotImplementedError

    @abstractmethod
    def stop_module(self):
        """Stop module"""
        raise NotImplementedError

    
    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
    
class LauncherContext():
    """ModuleLauncher factory; Instantiate a ModuleLauncher given a module"""

    @staticmethod
    def get_launcher(module: Module) -> ModuleLauncher:
        """
            ModuleLauncher factory method; gets launcher based on filetype
        """

        # get launcher settings
        ls = settings.launcher.get(module.filetype)
        if not ls:
            raise LauncherException(f"No launcher configured for type {module.filetype}")

        # create launcher instance from settings
        logger.debug(f"Importing {ls.get('class')}")
        mlauncher = ClassUtils.class_instance_from_settings_class_path(
                            f"launcher.{module.filetype}.class", launcher_settings=ls, module=module)
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
    def get_qos_config(self, **kwargs) -> dict:
        """Return the config given a request parameters"""
        raise NotImplementedError