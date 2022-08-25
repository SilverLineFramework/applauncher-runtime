"""
*TL;DR
Start docker containers;
"""
import socket
import docker

from common import LauncherException
from .launcher import QoSParams

class DockerClient(QoSParams):
    """
        Docker client wrapper. Implements QoSParams interface to return
        docker-specific qos config
    """
    # where to find run options in settings and default vaules
    _IMAGE_OPTS = { 'key': 'image', 'dft_opts': 'python' }

    # where to find run options in settings and default vaules
    _RUN_OPTS = { 'key': 'run_opts', 'dft_opts': {
                    'auto_remove': True,
                    'stdin_open': True,
                    'detach': True,
                    'cap-drop': all }}

    # where to find qos options in settings and default vaules
    _QOS_OPTS = { 'key': 'dft_qos', 'dft_opts': {
                    'cpu_count': 1,
                    'cpu_period': 100000,
                    'cpu-quota': 25000 }
                }

    def __init__(self, docker_settings: dict) -> None:
        # image to run
        self.image = docker_settings.get(
                            DockerClient._IMAGE_OPTS['key'],
                            DockerClient._IMAGE_OPTS['dft_opts'])
        # options we use to run our containers
        self._run_opts = docker_settings.get(
                            DockerClient._RUN_OPTS['key'],
                            DockerClient._RUN_OPTS['dft_opts'])
        # default qos options we use to run our containers
        self._dft_qos_opts = docker_settings.get(
                            DockerClient._QOS_OPTS['key'],
                            DockerClient._QOS_OPTS['dft_opts'])
        try:
            self._client = docker.from_env()
        except docker.errors.DockerException as docker_exception:
            raise LauncherException(f"[Launcher] Error starting docker \
                    (is docker running ?). {docker_exception}") from docker_exception

    def start_attached(self, image: str, command: str, **kwargs) -> socket.SocketIO:
        """
            Start command on container image with options received and stdin/stdout attached to
            a socket
            This call returns immediately the socket attached to the container's stdin/stdout
            Arguments are passed to docker run:
            https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

            Arguments
            ---------
                image:
                    container image
                command:
                    command to execute on the container
                kwargs:
                    User options passed to docker run as follows:
                    https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

            Returns
                A socket attached to the container's stdin/stdout
        """
        # merge user options with ours such; ours will override user options
        run_options = {**kwargs, **self._run_opts}

        # run container
        container = self._client.containers.run(image, command, run_options)

        # attach socket
        sock = container.attach_socket(params={'stdin': 1, 'stdout': 1, 'stream':1})

        return sock

    def get_qos_config(self, **kwargs):
        """Given a request, return docker-specific qos parameters"""
        # TODO: QoS according to module properties; Add real-time config:
        # https://docs.docker.com/config/containers/resource_constraints/#configure-the-realtime-scheduler
        return self._dft_qos_opts
