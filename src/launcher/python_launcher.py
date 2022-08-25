"""
*TL;DR
Implements a launcher for a python program;
Prepares the program files and container to run the pythom program
"""

from typing import Dict
import importlib
from logzero import logger

from model import Module
from common import settings, ClassUtils
from .launcher import ModuleLauncher
from .docker_client import DockerClient

class PythonLauncher(ModuleLauncher):
    """
        Implements a launcher for python programs that starts the python programs in a container
        (filetype='PY' as mapped in .appsettings.py)
    """
    def __init__(self, launcher_settings: Dict, module: Module) -> None:
        self._settings = launcher_settings
        self._module = module

        # create repo builder instance from settings option
        self._file_repo = ClassUtils.class_instance_from_settings_class_path('repository.class', do_cleanup=False)

        # get docker client instance
        self._docker_client = DockerClient(launcher_settings.get('docker'))

    def start_module(self):
        """Start module"""
        # get files
        print(self._module)
        self._file_repo.from_module_filename(settings.repository.url, self._module.filename)
        files_info = self._file_repo.get_files(True)
        print(files_info)
        

    def stop_module(self):
        """Stop module"""
        raise NotImplementedError
