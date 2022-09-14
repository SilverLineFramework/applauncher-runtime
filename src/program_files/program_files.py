"""
Program files are collected (downloaded/copied/compressed/...) into a destination folder or tar file
"""
from typing import Optional
import tempfile
import os
import shutil
from pathlib import Path
import tarfile

from common import ProgramFileException
from .file_action import FileInfo, FileAction, FileDownloadAction

class ProgramFilesInfo:
    """Hold information about program files;
       files will be either on a folder given by path (by default a tmp folder) or a tarfile
       allows to add additional files needed for a program (e.g. add token files)
       assumes a builder that:
         -creates an instance pointing an empty folder where the files
          are going to be (default is to create a temporary folder)
         -adds file actions (FileAction instances):
            -at least once: calls add_file() (possibly several times) to add a file
             (a FileAction) to folder
         -calls get_files() to get the files; file actions are executed and files
          are downloaded/copied/compressed/...
    """
    _FILES_FOLDER = 'files' # files are downloaded/copied to this folder inside self._base_path
    _TAR_FILENAME = 'files.tar.gz'

    # declare types of instance variables
    _base_path: Path
    _tar_filepath: Optional[Path]=None
    _file_actions: "list[FileAction]"
    _files: "list[FileInfo]"

    def __init__(self, base_path: str=None, do_cleanup: bool=True) -> None:
        """
        Init object; Make sure path exists and is an empty folder
        Arguments:
            path: destination folder
        """
        
        # if we should delete files
        self._do_cleanup = do_cleanup
        
        # create path if needed
        if not base_path:
            base_path = tempfile.mkdtemp()

        # destination folder (creating a Path object to ensure it is a valid path)
        self._base_path = Path(base_path)

        if not os.path.exists(self._base_path):
            os.makedirs(self._base_path)
        else:
            folder_files = os.listdir(self._base_path)
            if not len(folder_files) == 0:
                raise ProgramFileException(f"Destination program file \
                                        folder ({self._base_path}) not empty!")

        # create files folder (inside path)
        os.makedirs(self.path)

        # array of FileActions to execute on get_files()
        self._file_actions = []

        # array of file info filled on get_files()
        self._files = []

    def __del__(self) -> None:
        """ Remove files """
        # only perform cleanup if do_cleanup=True
        if not self._do_cleanup: return
        
        # remove files
        for fa in self._file_actions:
            if os.path.exists(fa.file.path):
                os.remove(fa.file.path)
            # remove 'source_path' temporary files too
            if fa.file.tmp and os.path.exists(fa.file.source_path):
                os.remove(fa.file.source_path)

        # delete tar
        if self._tar_filepath:
            os.remove(self._tar_filepath)

        # delete entire folder just in case
        try:
            shutil.rmtree(self._base_path)
        except FileNotFoundError:
            pass

    def add_file(self,
                source: Path,
                dest: Path,
                action: FileAction=FileDownloadAction,
                tmp: bool=False) -> None:
        """ Add a file to file actions list; file actions will
            be executed on get_files()
        """
        file_action = action(FileInfo(source, dest, tmp))
        self._file_actions.append(file_action)

    def tar_files(self, tar_filepath: str=None) -> None:
        """ Create a tar of the files """
        # did we tar the files previously ?
        if self._tar_filepath:
            os.remove(self._tar_filepath)

        if not tar_filepath:
            tar_fp = Path(self._base_path).joinpath(ProgramFilesInfo._TAR_FILENAME)
            #tempfile.mkstemp(dir=self._base_path, suffix=ProgramFilesInfo._TAR_SUFFIX)
        else:
            tar_fp = Path(tar_filepath)

        self._tar_dir(self.path, tar_fp)

        # save tar path
        self._tar_filepath = tar_fp

    def _tar_dir(self, path: Path, tar_filepath: Path) -> None:
        """Create a tar from path (path includes filename)"""
        with tarfile.open(tar_filepath, "w:gz") as tf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    tf.add(os.path.join(root, file), arcname=file)
            tf.close()

    def get_files(self):
        """Execute actions on file actions list downloading/copying/... files"""
        for fa in self._file_actions:
            fi = fa.execute()
            self._files.append(fi) # add file info to files list

        # clear file actions
        self._file_actions = []

    @property
    def path(self) -> Path:
        """Return the base path to where files are """
        return Path(self._base_path).joinpath(ProgramFilesInfo._FILES_FOLDER)

    @property
    def files(self) -> "list[FileInfo]":
        """Return the list of files """
        return self._files

    @property
    def tar_filepath(self) -> Path:
        """Return the path to the tar file, if created """
        return self._tar_filepath

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
