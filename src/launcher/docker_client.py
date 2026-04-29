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
import subprocess
import json
import requests

from common import LauncherException
from .launcher import QoSParams

class DockerContainerStatus(str, Enum):
    """Docker container statuses enum; TODO: add more."""
    created = 'created'
    restarting = 'restarting'
    running = 'running'
    removing = 'removing'
    paused = 'paused'
    exited = 'exited'
    dead = 'dead'

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
                    #'cpu_count': 1,
                    #'cpu_period': 100000,
                    #'cpu_quota': 25000 
                    }
                }
    # attach_socket options: include stdin, stdout, stderr
    _CTN_SOCK_OPTS = {'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream': 1}
    
    def __init__(self, **kwargs) -> None:
        self._settings = kwargs
        self._container = None
        self._stats: Dict[str, float] = {}
        
        # image to run
        self.image = self._settings.get(
                            DockerClient._IMAGE_OPTS['key'],
                            DockerClient._IMAGE_OPTS['dft_opts'])
        
        # options we use to run our containers; user settings override defaults
        self._run_opts = { **DockerClient._RUN_OPTS['dft_opts'], **self._settings.get( DockerClient._RUN_OPTS['key'], {} )}
        
        try:
            self._client = docker.from_env()
        except docker.errors.DockerException as docker_exception:
            raise LauncherException(f"[DockerClient] Error starting docker (is the docker daemon running ?). {docker_exception}") from docker_exception
        
    def wait_for_container(self, container, exit_notify_call):
        """Called within dedicated thread to wait for a container to exit"""

        try:
            container.wait()
        except docker.errors.NotFound:
            logger.warning("Container exited before we could wait on it.")

        exit_notify_call()
        
    def __del__(self) -> None:
        """ Cleanup """
        # cleanup container
        if self._container:     
            try:
                self._container.stop() # should delete the container; auto_remove = True
            except docker.errors.NotFound as docker_err:
                # container might be stopped already; skipping for now
                pass 

    def start_attached(self, command: str, id: str=None, workdir_mount_source: str=None, exit_notify: Callable=None, **kwargs) -> socket.SocketIO:
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
        if id is None:
            id = str(uuid.uuid4())

        if workdir_mount_source:
            if 'volumes' in kwargs:
                # append workdir mount to caller-provided volumes
                kwargs['volumes'].append( f"{workdir_mount_source}:{self._settings['workdir']}" )
            else:
                kwargs['volumes'] = [ f"{workdir_mount_source}:{self._settings['workdir']}" ]
                            
        # merge user options with ours such; ours will override user options
        run_options = {'image':self.image, 'command': command, **self._run_opts, **kwargs}

        # run container
        self._container = self._client.containers.run(**run_options) 

        # attach socket
        sock = self._container.attach_socket(params=DockerClient._CTN_SOCK_OPTS)

        # setup thread to wait for container to exit
        if exit_notify:
            monitor_thread = threading.Thread(target=self.wait_for_container, args=(self._container,exit_notify))
            monitor_thread.start()
          
        # init stats
        self._stats = { 'previous_cpu': 0.0, 'previous_system': 0.0 }
        
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

    def __get_blkio_stats(self, d: Dict) -> int:
        """Return total block I/O bytes (read + write) from docker stats."""
        entries = (d.get("blkio_stats") or {}).get("io_service_bytes_recursive") or []
        return sum(e.get("value", 0) for e in entries)

    def __get_network_stats(self, d: Dict) -> Dict:
        """ Get network bytes from docker stats
            adapted from: https://github.com/TomasTomecek/sen/blob/62a6d26fcbf40e32f8c39a9754143f3ec1c83bb9/sen/util.py#L210
        """
        networks = d.get("networks", None)
        if not networks:
            return { 'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0 }
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

    def get_stats(self) -> Dict:
        if not self._container:
            raise LauncherException(f"[DockerClient] Container not running!")
        
        try: 
            ctn_stats = self._container.stats(decode=False, stream=False)
        except docker.errors.NotFound:
            raise LauncherException(f"[DockerClient] Container not running!")
        except requests.exceptions.JSONDecodeError:
            raise LauncherException(f"[DockerClient] Decode error!")
        #cpu_percent, self._stats['previous_cpu'], self._stats['previous_system'] = self.__get_cpu_stats(ctn_stats, self._stats['previous_cpu'], self._stats['previous_system'])
        net_stats = self.__get_network_stats(ctn_stats)

        stats_cmd = ['docker', 'stats', '--no-stream', self._container.id, '--format', '{{ json . }}']
        result = subprocess.run(stats_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            dstats = json.loads(result.stdout.decode('utf-8'))
        except json.JSONDecodeError:
            return { **ctn_stats, 'cpu_percent': None, 'mem_usage': None, **net_stats }

        mem_usage_bytes = 0.0
        try:
            mem_str = dstats['MemUsage'].split('/', 1)[0].strip()
            for suffix, mult in [('GiB', 1e9), ('MiB', 1e6), ('KiB', 1e3), ('B', 1)]:
                if mem_str.endswith(suffix):
                    mem_usage_bytes = float(mem_str[:-len(suffix)]) * mult
                    break
        except (ValueError, KeyError):
            pass

        cpu_percent = 0.0
        try:
            cpu_percent = float(dstats['CPUPerc'].replace("%", ""))
        except ValueError:
            pass
            
        blkio_bytes = self.__get_blkio_stats(ctn_stats)
        stats = { **ctn_stats, 'cpu_percent': cpu_percent, 'mem_usage': mem_usage_bytes, 'blkio_bytes': blkio_bytes, **net_stats }
        
        return stats
    
    def stop(self):
        if not self._container:
            raise LauncherException(f"[DockerClient] Container not running!")

        try:
            self._container.stop()
        except docker.errors.NotFound as docker_err:
            raise LauncherException(f"[DockerClient] Container not running!") from docker_err

    def kill(self):
        if not self._container:
            raise LauncherException(f"[DockerClient] Container not running!")

        try:
            self._container.kill()
        except docker.errors.NotFound as docker_err:
            raise LauncherException(f"[DockerClient] Container not running!") from docker_err

    def is_running(self):
        """ return True if container is running; False otherwise
        """
        if not self._container:
            return False
        
        status = self._container.status
        
        if status == DockerContainerStatus.running: 
            return True
        
        return False
        
    def get_qos_config(self, **kwargs):
        """Given a request, return docker-specific qos parameters"""
        # TODO: QoS according to module properties; Add real-time config:
        # https://docs.docker.com/config/containers/resource_constraints/#configure-the-realtime-scheduler
        return {}
