"""
Download program files from repository
TODO: support different types/versions of repo
"""
#import pywebcopy
from abc import ABC, abstractmethod
import requests
import ssl
from bs4 import BeautifulSoup
from pathlib import Path
from logzero import logger
import tempfile
import shutil
from urllib.parse import urlparse
from urllib.request import urlopen
import os
import shutil
import tarfile
from enum import Enum

from common.config import settings

class FilestoreRepository:
    """Download files from file repository."""

    _description = 'ARENA filestore repo v0'

    def __init__(self):

        self.url = settings.get("repository.args.url")

    def get_program_tar(self, pn):
        """Downloads program; Return program tar file path from program name."""
        td = self.get_files(self._program_url(pn))
        print(td)

    def _program_url(self, pn):
        """Return program full URL from program name."""
        url = f"{self.url}/users/{pn}"
        if not url.endswith('/'): url += '/'
        return url
