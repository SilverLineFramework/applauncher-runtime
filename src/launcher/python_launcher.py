"""
*TL;DR
Implements a launcher for a python program inside a container;
Prepares the program files and container to run the python program.
Instanciates a docker client to startup the container. 

We instanciate a launcher and a docker client for each module (this 
allows for for better error recovery; e.g. a module might fail to 
start due to unavailability of the docker service, a later retry 
will be successful when docker service comes back up; we dont implement
these retries)
"""

from typing import Dict, Callable
import json
from logzero import logger
from pathlib import Path
import re

from model import Module, ModuleStats
from common import settings, ClassUtils
from common import LauncherException
from .launcher import ModuleLauncher
from .docker_client import DockerClient
from pubsub import PubsubStreamer, PubsubListner

class PythonLauncher(ModuleLauncher):
    """
        Implements a launcher for python programs that starts the python programs in a container
        (filetype='PY' as mapped in .appsettings.py)
    """
         
    def __init__(self, launcher_settings: Dict, module: Module, pubsubc: PubsubListner = None) -> None:
        """
            Init a python launcher for a module receiving laucher settings as argument and the module data
            Save info to setup a streamer to publish/subcribe stdin, stdout, stderr of the module

            Arguments
            ---------
                launcher_settings:
                    dictionary of launcher settings
                module:
                    module object
                pubsubc:
                    a pubsub client object the streamer uses to publish messages
        """        
        self._settings = launcher_settings
        self._module = module
        self._ctn_sock = None
        if settings.launcher.pipe_stdout: self._pubsubc = pubsubc
        else: self._pubsubc = None

        # create repo builder instance from settings option
        self._file_repo = ClassUtils.class_instance_from_settings_class_path('repository.class', do_cleanup=False)

        # get docker client instance
        self._docker_client = DockerClient(launcher_settings.docker)
             
    def start_module(self, exit_notify: Callable=None):
        """
            Start the module; Optionally accepts the setup data for a streamer to 
            publish/subcribe stdin, stdout, stderr of the module
            
            Arguments
            ---------
                exit_notify:
                    a callable to deliver container exit notification to
        """    
        # write auth token for arena-py; TODO: auth token should come from request
        auth_token_json = json.dumps({ 'username': settings.get('mqtt', {'username': 'nouser'}).get('username', ""), 'token': settings.get('mqtt', {'password': 'nouser'}).get('password', "")})
        self._file_repo.file_from_string_contents(auth_token_json, '.arena_mqtt_auth')
    
        # get the files from repo url base on module name (this creates a list of files to download)
        self._file_repo.from_module_data(settings.repository.url, self._module)
        
        # get the files into a tmp folder at files_info.path (this acctualy downloads the files)
        self._files_info = self._file_repo.get_files()
            
        # create a Path object to get program file from last component of file
        fnp = Path(self._module.file)
        
        # container cmd should accept the filename and list of arguments (which can be a list or a string) 
        cmd = [self._settings.cmd, fnp.name] + (self._module.args.split() if isinstance(self._module.args, str) else self._module.args)
    
        # add launcher env entries
        mod_env = self._module.env
        if settings.launcher.env:
            for evar in settings.launcher.env.split(' '):
                if isinstance(mod_env, dict):
                    evar_splitted = evar.split('=')
                    if len(evar_splitted) == 2: mod_env[evar_splitted[0]] = evar_splitted[1]
                elif isinstance(mod_env, list):
                    mod_env.append(evar)
                else:
                    logger.warn("Module env must be a dictionary or a list")
                    
        # add PROGRAM_OBJECT_ID
        mod_env.append(f"PROGRAM_OBJECT_ID={self._module.uuid}")

        logger.debug(f"Starting module {self._module.name}. cmd: {cmd}, env: {mod_env}")
    
        # prepare parameters to start container
        start_attached_params = { 
                        'command': cmd,
                        'id': self._module.uuid,
                        'environment': mod_env,
                        'workdir_mount_source': str(self._files_info.path),
                        'exit_notify': exit_notify }
        
        # add container name if force_container_name is true in launcher settings
        # contrary to module names, container names are unique so this is mostly for debug purposes (defaults to False)
        if self._settings.docker.force_container_name: start_attached_params['name'] = re.sub('[^A-Za-z0-9]+', '', self._module.name) 

        # start container with stdin, stdout, stderr attached to a socket
        self._ctn_sock = self._docker_client.start_attached(**start_attached_params)

        # start pubsub streamer that will publish/subscribe stdin, stdout, stderr topics
        if self._pubsubc:
            self._streamer = PubsubStreamer(self._pubsubc, self._ctn_sock, self._module.topics)
                     
    def get_stats(self) -> ModuleStats:
        try:
            docker_stats = self._docker_client.get_stats()
        except LauncherException:
            logger.warn(f"get_stats: Module not found ({self._module.uuid})")
            return None

        # convert into ModuleStats
        return ModuleStats( cpu_usage_percent=docker_stats['cpu_percent'],
                           mem_usage=docker_stats['mem_usage'], 
                           network_rx_mb=docker_stats['rx_bytes']/1000000,
                           network_tx_mb=docker_stats['tx_bytes']/1000000,
                           network_rx_pkts=docker_stats['rx_packets'],
                           network_tx_pkts=docker_stats['tx_packets'],
                        )
        
    def is_created_or_running(self) -> bool:
        return self._docker_client.is_created_or_running()
    
    def get_settings(self) -> Dict:
        return self._settings
    
    def stop_module(self):
        """Stop module"""
        logger.debug(f"Stopping module {self._module.name}.")
        self._docker_client.stop()
