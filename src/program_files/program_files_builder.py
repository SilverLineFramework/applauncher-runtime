"""
*TL;DR
Define interface a program builder should implement
TODO: review; possibly too Filestore-specific ?
"""

from abc import abstractmethod, abstractproperty
from typing import Protocol

class ProgramFilesBuilder(Protocol):
    """ ProgramFilesBuilder interface """

    @property
    @abstractmethod
    def _description(self):
        pass

    @abstractmethod
    def reset(self):
        """ Reset builder state """

    @abstractmethod
    def from_module_data(self, store_base_url, module):
        """Get files from module data in the form """
        
    @abstractmethod
    def from_url(self, url):
        """Get files listed from 'from_url' """

    @abstractmethod
    def copy_file(self, source_path: str, source_file: str, dest_path: str=""):
        """Add file to files list; it will be copied in get_files
            Arguments:
                source_filepath : fullpath to where the file is, including filename
                dest_filepath   : path to destination file relative to _files_info.path
                                  if not given or does not include the filename, a
                                  name will added based on the source_filepath
        """

    @abstractmethod
    def file_from_string_contents(self, str_contents: str, dest_filepath: str):
        """
            Create tmp file with str_contents and add to files list; it will be copied in get_files
            Arguments:
                str_contents    : contents of the file
                dest_filepath   : path to destination file relative to _files_info.base_path;
                                  MUST include the filename
        """

    @abstractmethod
    def get_files(self, tar_files: bool=False):
        """ Get program files from repository """
