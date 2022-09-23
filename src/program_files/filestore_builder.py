"""
*TL;DR
Implements a ProgramFilesBuilder for the ARENA filestore
"""
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError
from pathlib import Path
import ssl
from bs4 import BeautifulSoup
from logzero import logger

from common import ProgramFileException
from .program_files_builder import ProgramFilesBuilder
from .program_files import ProgramFilesInfo
from .file_action import FileCopyAction

class FileStoreBuilder(ProgramFilesBuilder):
    """
        ProgramFilesInfo builder; knows how to create ProgramFilesInfo instances from a filestore
        After get_files, is ready to create another instance
        TODO: create builders (ProgramFilesBuilder) for different repositories
    """

    _description = 'ARENA filestore repo v0'

    def __init__(self, do_cleanup=True) -> None:
        self.reset(do_cleanup)

    def reset(self, do_cleanup=True) -> None:
        # new instance of program files
        self._files_info = ProgramFilesInfo(do_cleanup=do_cleanup)

    def from_module_name(self, store_base_url: str, module_name: str) -> None:
        """Get files from  module name in the form username/module_folder            
           NOTE: Creates the full url and calls from_url(); assumes directory index listing is enabled on the webserver
        """
        url = f"{store_base_url}/users/{module_name}" # TODO: better handling of this path concat
        self.from_url(url)

    def from_module_filename(self, store_base_url: str, module_filename: str) -> None:
        """Get files from module filename in the form username/module_folder/program_entry_file            
           NOTE: Creates the full url and calls from_url(); assumes directory index listing is enabled on the webserver
        """
        fn_path = Path(module_filename)
        url = f"{store_base_url}/users/{fn_path.parent}" # TODO: better handling of this path concat
        self.from_url(url)
        
    def __from_url(self, url: str, base_path: str) -> int:
        """Internal get files from url to be called recursively
        """

        # make sure URL has a trailing /
        if not url.endswith('/'):
            url = url + '/'

        logger.debug(f"Getting files from: {url} to {self._files_info.path}/{base_path}")

        # download to folder inside given path
        try: 
            index_data = urlopen(url, context=ssl._create_unverified_context()).read()
        except HTTPError as http_error:
            raise ProgramFileException(f"Error fetching {url}. Detail: {http_error}") from http_error
        
        index_parsed = BeautifulSoup(index_data, "html.parser")
        links = index_parsed.find_all('a')
        if len(links) == 0:
            raise ProgramFileException(f"Program files listing returned empty: {url} (is directory index listing is enabled on the webserver ?)")
        count=0
        for file_link in links:
            file_href = file_link.get('href')
            if not file_href == '../':
                if file_href.endswith('/'):
                    new_base_path = base_path.join(file_href)
                    parsed_url = urlparse(f"{url}{file_href}")
                    count = count + self.__from_url(parsed_url.geturl(), new_base_path)
                else:
                    filename = Path(self._files_info.path).joinpath(Path(f"{base_path}{file_href}"))
                    # add file download url using default download action
                    self._files_info.add_file(f"{url}{file_href}", filename)
                    count += 1
        if count == 0:
            raise ProgramFileException(f"No program files to download at: {url}.")
        return count

    def from_url(self, url: str) -> None:
        """Get files listed in 'from_url' index.html and add to files list
           files list will be processed in get_files
           NOTE: assumes directory index listing is enabled on the webserver
        """
        return self.__from_url(url, "")

    def copy_file(self, source_path: str, source_file: str, dest_path: str="") -> None:
        """
            Add file to files list; it will be copied in get_files
            Arguments:
                source_path : path to where the file is
                source_file : source filename
                dest_path : destination path, **not including filename** to destination folder relative to _files_info.path
                            if not given, file will added to _files_info.path
        """
        sfp = Path(source_path).joinpath(source_file)

        # treat dest_path as a relative path to _files_info.path
        dfp = self._files_info.path.joinpath(dest_path, source_file)
        
        self._files_info.add_file(sfp, dfp, FileCopyAction)

    def file_from_string_contents(self, str_contents: str, dest_filepath: str) -> None:
        """
            Create tmp file with str_contents and add to files list; it will be copied in get_files
            Arguments:
                str_contents    : contents of the file
                dest_filepath   : path to destination file relative to
                                _files_info.path; MUST include the filename
        """
        # treat dest_filepath as a relative path to _files_info.path
        dfp = Path(self._files_info.path).joinpath(dest_filepath)

        if not dfp.name:
            raise ProgramFileException("No valid destination filepath given!")

        # creates a temporary file; the user of mkstemp() is responsible for deleting the temporary file when done with it.
        (fd, source_filepath) = tempfile.mkstemp(text=True)
        file = open(fd, 'wt')
        file.write(str_contents)
        file.close()

        # add file to be copied (copy action) and mark as tmp (so it is deleted after copy)
        self._files_info.add_file(Path(source_filepath), Path(dfp), FileCopyAction, False)

    def get_files(self, tar_files: bool=False) -> ProgramFilesInfo:
        """
            Get files; Execute file actions and optionally compress the files
            After this call, resets the state and is ready to create another
            ProgramFilesInfo instance
            Return:
                ProgramFilesInfo instance
        """
        self._files_info.get_files()

        if tar_files:
            self._files_info.tar_files()

        fi = self._files_info
        self.reset()

        # return the built instance
        return fi
