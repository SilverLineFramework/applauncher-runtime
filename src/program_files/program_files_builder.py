"""
*TL;DR
Define interface a program builder should implement
TODO: review; possibly too Filestore-specific ?
"""

from abc import ABC, abstractmethod, abstractproperty

class ProgramFilesBuilder(ABC):
    """ ProgramFilesBuilder abstract class """

    @abstractproperty
    def _description(self):
        pass

    @abstractmethod
    def reset(self):
        """ Reset builder state """
        pass

    @abstractmethod
    def from_url(self, url):
        """Get files listed from 'from_url' """
        pass

    @abstractmethod
    def copy_file(self, source_filepath, dest_filepath=""):
        """Add file to files list; it will be copied in get_files
            Arguments:
                source_filepath : fullpath to where the file is, including filename
                dest_filepath   : path to destination file relative to _files_info.path
                                  if not given or does not include the filename, a name will added based on the source_filepath
        """
        pass

    @abstractmethod
    def file_from_string_contents(self, str_contents, dest_filepath):
        """
            Create tmp file with str_contents and add to files list; it will be copied in get_files
            Arguments:
                str_contents    : contents of the file
                dest_filepath   : path to destination file relative to _files_info.base_path; MUST include the filename
        """
        pass

    @abstractmethod
    def get_files(self, tar_files=False):
        """ Get program files from repository """
        pass
