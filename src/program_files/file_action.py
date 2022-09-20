"""
Actions (copy/download) executed on a program file
"""

from abc import abstractmethod
from typing import Protocol
import os
from pathlib import Path
import shutil
import requests
class FileInfo():
    """Hold information about a file that we apply an action to"""

    # declare types of instance variables
    _source_path: Path
    _path: Path
    _tmp: bool

    def __init__(self, source: Path, dest: Path, tmp=False) -> None:
        """
        Arguments:
            source: where to get the file (download url/path to copy or compress from)
            dest: (destination) path of the file once we execute the action
            tmp: indicates if the source file is temporary (so we can delete it)
        """
        self._source_path = source
        self._path = dest
        self._tmp = tmp

    @property
    def source_path(self) -> Path:
        return self._source_path

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: Path):
        self._path = path

    @property
    def tmp(self) -> bool:
        return self._tmp

    def __str__(self) -> str:
        #return str(self.__class__) + ": " + str(self.__dict__)
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

class FileAction(Protocol):
    """ FileAction abstract class; FileActions have a method for executing an action. """
     
    @abstractmethod
    def execute(self):
        pass

    @property    
    @abstractmethod
    def file(self) -> FileInfo:
        pass

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

class FileDownloadAction(FileAction):
    """
    Download a file indicated by FileInfo.source_path to a file at FileInfo.path
    """
    def __init__(self, file: FileInfo) -> None:
        self._file = file

    @property
    def file(self) -> FileInfo:
        return self._file

    def execute(self) -> FileInfo:
        response = requests.get(self._file.source_path)
        os.makedirs(os.path.dirname(self._file.path), exist_ok=True)
        f = open(self._file.path, "wb")
        f.write(response.content)
        f.close()

        return self._file

class FileCopyAction(FileAction):
    """
    Copy a file indicated by FileInfo.source_path to a file at FileInfo.path
    """
    def __init__(self, file: FileInfo) -> None:
        self._file = file

    @property
    def file(self) -> FileInfo:
        return self._file

    def execute(self) -> FileInfo:
        shutil.copy2(self._file.source_path, self._file.path)
        # tmp files are delete after copy
        if self._file.tmp and os.path.exists(self._file.source_path):
            os.remove(self._file.source_path)

        return self._file

# class TarFolderAction(FileAction):
#     """
#     Tar a *folder* indicated by the FileInfo.source_path to a file at FileInfo.path
#     if FileInfo.path is not given, will create a (temporary) destination file
#     """
#
#     _TAR_SUFFIX = '.tar.gz'
#
#     def __init__(self, file: FileInfo):
#         self._file = file
#
#         # create destination file if not given
#         if not self._file._path:
#             (tarfile_handle, self._file._path) = tempfile.mkstemp(suffix=self._TAR_SUFFIX)
#
#         return self._file._path
#
#     def _tar_dir(self, path, tar_path):
#         """Create a tar from path (path includes filename)"""
#
#         with tarfile.open(tar_path, "w:gz") as tf:
#             for root, dirs, files in os.walk(path):
#                 for file in files:
#                     tf.add(os.path.join(root, file))
#             tf.close()
#
#     def execute(self):
#         # check if source (FileInfo.source_path) exists and is a folder
#         if not os.path.isfile(self._file.source_path):
#             raise ProgramFileException("Tar source folder does not exist!")
#         if not os.path.isdir(self._file.source_path):
#             raise ProgramFileException("Tar source is not a folder!")
#
#         self._tar_dir(self._file.source_path)
#
#         return self._file
