"""
*TL;DR
Implements a ProgramFilesBuilder for the ARENA filestore
"""
import requests
import ssl
from bs4 import BeautifulSoup
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
from pathlib import Path

from .program_files_builder import ProgramFilesBuilder
from .program_files import ProgramFilesInfo
from .file_action import FileInfo, FileDownloadAction, FileCopyAction

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
