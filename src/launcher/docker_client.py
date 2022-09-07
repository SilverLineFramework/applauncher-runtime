"""
*TL;DR
Start docker containers;
"""
from typing import List, Callable, Dict, Tuple
import socket
import docker
import threading
from enum import Enum
from logzero import logger
import uuid

from common import LauncherException
from .launcher import QoSParams

class DockerContainerStatus(str, Enum):
    """Docker container statuses enum; TODO: add more."""
    created = 'created',
    restarting = 'restarting', 
    running = 'running'
    removing = 'removing',
    paused = 'paused', 
    exited = 'exited',
    dead = 'dead',

class DockerClient(QoSParams):
    """
        Docker client wrapper. Implements QoSParams interface to return
        docker-specific qos config
    """
    # where to find run options in settings and default vaules 
    # (TODO: rely on Dynaconf validator and defaults, if possible)
    _IMAGE_OPTS = { 'key': 'image', 'dft_opts': 'python' }

    # where to find run options in settings and default vaules
    # (TODO: rely on Dynaconf validator and defaults, if possible)
    _RUN_OPTS = { 'key': 'run_opts', 'dft_opts': {
                    'auto_remove': True,
                    'stdin_open': True,
                    'detach': True,
                    #'cap_drop': 'all',
                    'working_dir': '/usr/src/app',
                    'cpu_count': 1,
                    'cpu_period': 100000,
                    'cpu_quota': 25000 }
                }
    # attach_socket options: include stdin, stdout, stderr
    _CTN_SOCK_OPTS = {'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream': 1}
    
    def __init__(self, docker_settings: dict) -> None:
        self._settings = docker_settings
        self._containers = {}
        self._stats = {}
        
        # image to run
        self.image = self._settings.get(
                            DockerClient._IMAGE_OPTS['key'],
                            DockerClient._IMAGE_OPTS['dft_opts'])
        
        # options we use to run our containers
        self._run_opts = { **self._settings.get( DockerClient._RUN_OPTS['key'], {} ), **DockerClient._RUN_OPTS['dft_opts']}
        
        try:
            self._client = docker.from_env()
        except docker.errors.DockerException as docker_exception:
            raise LauncherException(f"[DockerClient] Error starting docker (is docker running ?). {docker_exception}") from docker_exception
        
    def wait_for_container(self, container, notify_call):
        """Called within dedicated thread to wait for a container to exit"""
        container.wait(timeout=None, condition='not-running')
        # container exited; perform notification call given
        notify_call()
        
    def __del__(self) -> None:
        """ Cleanup """
        # cleanup containers
        for key in self._containers:
            self._containers[key].stop() # should delete the container; auto_remove = True

    def start_attached(self, command: str, id: str=str(uuid.uuid4()), workdir_mount_source: str=None, exit_notify: Callable=None,  **kwargs) -> socket.SocketIO:
        """
            Start command on container image with options received and stdin/stdout attached to
            a socket
            This call returns immediately the socket attached to the container's stdin/stdout
            Arguments are passed to docker run:
            https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

            Arguments
            ---------
                command:
                    command to execute on the container
                id: 
                    caller-supplied identifier to later get the container
                workdir_mount_source:
                    host path where the container workdir will be mounted
                exit_notify:
                    a callable to deliver container exit notification to
                kwargs:
                    User options passed to docker run as follows:
                    https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

            Returns
                A socket attached to the container's stdin/stdout
        """
        if id in self._containers:
            raise LauncherException(f"[DockerClient] Duplicate ID supplied!")
        
        if workdir_mount_source:
            if 'volumes' in kwargs:
                # append workdir mount to caller-provided volumes
                kwargs['volumes'].append( f"{workdir_mount_source}:{self._settings['workdir']}" )
            else:
                kwargs['volumes'] = [ f"{workdir_mount_source}:{self._settings['workdir']}" ]
                            
        # merge user options with ours such; ours will override user options
        run_options = {**kwargs, **self._run_opts}

        # run container
        self._containers[id] = self._client.containers.run(image=self.image, command=command, **run_options)

        # attach socket
        sock = self._containers[id].attach_socket(params=DockerClient._CTN_SOCK_OPTS)

        # setup thread to wait for container to exit
        if exit_notify:
            monitor_thread = threading.Thread(target=self.wait_for_container, args=(self._containers[id],exit_notify))
            monitor_thread.start()
          
        # init stats
        self._stats[id] = { 'previous_cpu': 0.0, 'previous_system': 0.0 }
        
        return sock

    def __get_cpu_stats(self, d: Dict, previous_cpu: float, previous_system: float) -> Tuple:
        """ Get cpu percentage from docker stats
            from: https://github.com/TomasTomecek/sen/blob/62a6d26fcbf40e32f8c39a9754143f3ec1c83bb9/sen/util.py#L176
        """        
        cpu_percent = 0.0
        cpu_total = float(d["cpu_stats"]["cpu_usage"]["total_usage"])
        cpu_delta = cpu_total - previous_cpu
        cpu_system = float(d["cpu_stats"]["system_cpu_usage"])
        system_delta = cpu_system - previous_system
        online_cpus = d["cpu_stats"].get("online_cpus", len(d["cpu_stats"]["cpu_usage"].get("percpu_usage", [None])))
        if system_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
        return cpu_percent, cpu_system, cpu_total

    def __get_network_stats(self, d: Dict) -> Dict:
        """ Get network bytes from docker stats
            adapted from: https://github.com/TomasTomecek/sen/blob/62a6d26fcbf40e32f8c39a9754143f3ec1c83bb9/sen/util.py#L210
        """
        networks = d.get("networks", None)
        if not networks:
            return 0, 0
        rb = 0
        tb = 0
        rp = 0
        tp = 0
        for if_name, data in networks.items():
            rb += data["rx_bytes"]
            tb += data["tx_bytes"]
            rp += data["rx_packets"]
            tp += data["tx_packets"]
        return { 'rx_bytes': rb, 'tx_bytes': tb, 'rx_packets': rp, 'tx_packets': tp }

    def get_stats(self, id: str) -> Dict:
        if not id in self._containers:
            raise LauncherException(f"[DockerClient] Unknown ID supplied!")
        
        stats = self._containers[id].stats(decode=None, stream = False)
        cpu_percent, self._stats[id]['previous_cpu'], self._stats[id]['previous_system'] = self.__get_cpu_stats(stats, self._stats[id]['previous_cpu'], self._stats[id]['previous_system'])
        net_stats = self.__get_network_stats(stats)
        return { 'cpu_percent': cpu_percent, **net_stats }
    
    def stop(self, id: str):
        if not id in self._containers:
            raise LauncherException(f"[DockerClient] Unknown ID supplied!")
        
        ctrn = self._containers.pop(id)
        ctrn.stop()

    def is_created_or_running(self, id: str=None, ctnr=None):
        """ return True if container is created or running; False otherwise
            can receive id previously provided with start or a container reference
        """
        status = 'unknown'
        if id:
            if not id in self._containers:
                raise LauncherException(f"[DockerClient] Unknown ID supplied!")
        
            status = self._containers[id].status
        if ctnr:
            status = ctnr.status
        
        if status == DockerContainerStatus.running or status == DockerContainerStatus.created: 
            return True
        
        return False
        
    def get_qos_config(self, **kwargs):
        """Given a request, return docker-specific qos parameters"""
        # TODO: QoS according to module properties; Add real-time config:
        # https://docs.docker.com/config/containers/resource_constraints/#configure-the-realtime-scheduler
        return self._dft_qos_opts
