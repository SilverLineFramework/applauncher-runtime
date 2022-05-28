"""
Start docker containers
"""
import docker
from logzero import logger
import importlib

from common.config import settings
from.launcher_proto import Launcher

class DockerLauncher(Launcher):
    """Docker client wrapper.

    Parameters
    ----------
    """

    def __init__(self):
        self.client = docker.from_env()

        # create repo instance from settings option
        (repo_module, repo_class) = settings.get('repository.class').rsplit('.', 1)
        logger.debug("[Launcher] Importing {}.{}".format(repo_module, repo_class))
        RepoClass = getattr(importlib.import_module(repo_module), repo_class)
        self.file_repo = RepoClass()
        pass

    def module_start(self, module):
        """Start a module"""

        client.containers.run(settings.launcher.args.image, "echo hello world")
        pass
