"""
Program files are collected (downloaded/copied/compressed/...) into a destination folder or tar file
"""

from abc import ABC, abstractmethod, abstractproperty
import requests
import ssl
from bs4 import BeautifulSoup
from logzero import logger
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import os
import shutil
from pathlib import Path
import tarfile

from .file_action import FileInfo, FileDownloadAction, FileCopyAction#, TarFolderAction
from common.exception import ProgramFileException

class ProgramFilesInfo:
    """Hold information about program files;
       files will be either on a folder given by path (by default a tmp folder) or a tarfile
       allows to add additional files needed for a program (e.g. add token files)
       assumes a builder that:
         -creates an instance pointing an empty folder where the files are going to be (default is to create a temporary folder)
         -adds file actions (FileAction instances):
            -at least once: calls add_file() (possibly several times) to add a file (a FileAction) to folder
         -calls get_files() to get the files; file actions are executed and files are downloaded/copied/compressed/...
    """
    _FILES_FOLDER = 'files' # files are downloaded/copied to this folder inside self._base_path
    _TAR_FILENAME = 'files.tar.gz'

    def __init__(self, base_path=None):
        """
        Init object; Make sure path exists and is an empty folder
        Arguments:
            path: destination folder
        """
        # create path if needed
        if not base_path: base_path = tempfile.mkdtemp()


        # destination folder (creating a Path object guarantees it is a valid path)
        self._base_path = Path(base_path)

        if not os.path.exists(self._base_path):
            os.makedirs(self._base_path)
        else:
            folder_files = os.listdir(self._base_path)
            if not len(folder_files) == 0:
                raise ProgramFileException(f"Destination program file folder ({path}) not empty!")

        # create files folder (inside path)
        os.makedirs(self.path)

        # tar path, if crated
        self._tar_filepath = None

        # array of FileActions to execute on get_files()
        self._file_actions = []

        # array of file info filled on get_files()
        self._files = []

    def __del__(self):
        # remove files
        for fa in self._file_actions:
            if os.path.exists(fa._file.path): os.remove(fa._file.path)
            # remove 'source_path' temporary files too
            if fa._file.tmp and path.exists(fa._file.source_path):
                os.remove(fa._file.source_path)

        # delete tar
        if self._tar_filepath:
            os.remove(self._tar_filepath)

        # delete entire folder just in case
        try:
            shutil.rmtree(self._base_path)
        except FileNotFoundError:
            pass


    def add_file(self, source, dest, action=FileDownloadAction, tmp=False):
        file_action = action(FileInfo(source, dest, tmp))
        self._file_actions.append(file_action)

    def tar_files(self, tar_filepath=None):
        # did we tar the files previously ?
        if self._tar_filepath:
            os.remove(self._tar_filepath)

        if not tar_filepath:
            tar_filepath = Path(self._base_path).joinpath(ProgramFilesInfo._TAR_FILENAME)
            #tempfile.mkstemp(dir=self._base_path, suffix=ProgramFilesInfo._TAR_SUFFIX)
        else:
            tar_filepath = Path(tar_filepath)

        self._tar_dir(self.path, tar_filepath)

        # save tar path
        self._tar_filepath = tar_filepath

    def _tar_dir(self, path, tar_filepath):
        """Create a tar from path (path includes filename)"""
        with tarfile.open(tar_filepath, "w:gz") as tf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    tf.add(os.path.join(root, file))
            tf.close()

    def get_files(self):
        """Execute actions on file actions list downloading/copying/... files"""
        for fa in self._file_actions:
            fi = fa.execute()
            self._files.append(fi) # add file info to files list

        # clear file actions
        self._file_actions = []

    def file_fullpath(self, relative_filepath):
        """Return the fullpath given a path relative to _base_path"""
        return_path = Path(self.path).joinpath(relative_filepath)
        return return_path

    @property
    def path(self):
        return Path(self._base_path).joinpath(ProgramFilesInfo._FILES_FOLDER)

    @property
    def files(self):
        return self._files

    @property
    def tar_filepath(self):
        return self._tar_filepath

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

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
    def get_files(self):
        """ Get program files from repository """
        pass

class FileStoreBuilder(ProgramFilesBuilder):
    """
        ProgramFilesInfo builder; knows how to create ProgramFilesInfo instances from a filestore
        After get_files, is ready to create another instance
        TODO: create builders (ProgramFilesBuilder) for different repositories
    """

    _description = 'ARENA filestore repo v0'

    def __init__(self):
        self.reset()

    def reset(self):
        # new instance of program files
        self._files_info = ProgramFilesInfo()

    def from_url(self, url):
        """Get files listed in 'from_url' index.html and add to files list; it will be processed in get_files
           NOTE: assumes directory index listing is enabled on the webserver
        """
        # make sure URL has a trailing /
        if not url.endswith('/'): url = url + '/'

        # download to folder inside given path
        index_data = urlopen(url, context=ssl._create_unverified_context()).read()
        index_parsed = BeautifulSoup(index_data, "lxml")
        links = index_parsed.find_all('a')
        if len(links) == 0: raise ProgramFileException("Program files listing returned empty: {} (is directory index listing is enabled on the webserver ?)".format(url))
        count=0
        for file_link in links:
            file_href = file_link.get('href')
            if not file_href == '../':
                parsed_url = urlparse(f"{url}{file_href}")
                filename = Path(self._files_info.path).joinpath(Path(parsed_url.path).name)
                self._files_info.add_file(f"{url}{file_href}", filename) # add file download url using default download action
                count += 1
        if count == 0: raise ProgramFileException("No program files to download at: {}.".format(url))

    def copy_file(self, source_filepath, dest_filepath=""):
        """
            Add file to files list; it will be copied in get_files
            Arguments:
                source_filepath : fullpath to where the file is, including filename
                dest_filepath   : path to destination file relative to _files_info.path
                                  if not given or does not include the filename, a name will added based on the source_filepath
        """
        # treat dest_filepath as a relative path to _files_info.base_path
        if dest_filepath.startswith("/"):
            dest_filepath = dest_filepath[1:]

        sfp = Path(source_filepath)
        if not sfp.name:
            raise ProgramFileException("Source filepath does not include a filename!")

        dfp = Path(dest_filepath)
        if not dfp.name:
            dfp = Path(dest_filepath).joinpath(sfp.name)

        fp = self._files_info.file_fullpath(dfp)
        self._files_info.add_file(sfp, fp, FileCopyAction)

    def file_from_string_contents(self, str_contents, dest_filepath):
        """
            Create tmp file with str_contents and add to files list; it will be copied in get_files
            Arguments:
                str_contents    : contents of the file
                dest_filepath   : path to destination file relative to _files_info.base_path; MUST include the filename
        """
        # treat dest_filepath as a relative path to _files_info.base_path
        if dest_filepath.startswith("/"):
            dest_filepath = dest_filepath[1:]

        if len(dest_filepath) == 0:
            raise ProgramFileException("No valid destination filepath given")

        dfp = Path(dest_filepath)

        (file, source_filepath) = tempfile.mkstemp(text=True)
        n = file.write(str_contents)
        file.close()

        # add file to be copied (copy action) and mark as tmp (so it is deleted after copy)
        self._files_info.add_file(Path(source_filepath), Path(dest_filepath), FileCopyAction, True)

    def get_files(self, tar_files=False):
        """
            Get files; Execute file actions and optionally compress the files
            After this call, resets the state and is ready to create another ProgramFilesInfo instance
            Return:
                ProgramFilesInfo instance
        """
        self._files_info.get_files()

        if tar_files:
            self._files_info.tar_files()

        fi = self._files_info
        self.reset()

        # return the built intance
        return fi
