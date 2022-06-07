import unittest
from common.config import settings
import os

from program_files.filestore_builder import FileStoreBuilder
from program_files.file_action import FileInfo

class TestRepo(unittest.TestCase):
    def setUp(self):

        # test program to get files
        self.test_program_url = f"{settings.get('repository.url')}/users/arena/py/image-switcher"
        # test program files
        self.test_file_names = [ "image-switcher.py", "requirements.txt" ]
        # additional program files
        self.test_additional_files_path = f"{os.path.abspath(os.path.dirname(__file__))}/test_files"
        self.test_additional_files_name = [ "some_file.py", "some_text_file.txt" ]

    def _find_fileinfo_files(self, files_info, files, source_basepath):
        for fn in files:
            found = False
            for fi in files_info.files:
                if (    str(fi.source_path) == f"{source_basepath}/{fn}" and
                        str(fi.path) == f"{files_info.path}/{fn}" and
                        fi.tmp == False and
                        fi.path.is_file() ):
                    found = True
                    break
            self.assertTrue(found)

    def test_filestore_builder_downloads_files(self):
        # setup filestore and get files
        filestore = FileStoreBuilder()
        filestore.from_url(self.test_program_url)
        files_info = filestore.get_files()

        # check espected FileInfo file list
        self.assertTrue(len(files_info.files) == len(self.test_file_names)) # check len

        # check files
        self._find_fileinfo_files(files_info, self.test_file_names, self.test_program_url)

        pass

    def test_filestore_builder_adds_files(self):
        # setup filestore and get files
        filestore = FileStoreBuilder()
        filestore.from_url(self.test_program_url)

        # add files
        for afn in self.test_additional_files_name:
             # destination file will be in files root; name will be the same as source
            filestore.copy_file(f"{self.test_additional_files_path}/{afn}")

        # get files
        files_info = filestore.get_files()

        # check files
        self._find_fileinfo_files(files_info, self.test_additional_files_name, self.test_additional_files_path)

        pass

    def test_filestore_builder_tars_files(self):

        # setup filestore and get files
        filestore = FileStoreBuilder()
        filestore.from_url(self.test_program_url)

        # get files with tar_file = True
        files_info = filestore.get_files(True)

        # check tar exists
        self.assertTrue(os.path.isfile(files_info.tar_filepath))

        pass

    def test_filestore_builder_does_cleanup(self):

        # setup filestore and get files
        filestore = FileStoreBuilder()
        filestore.from_url(self.test_program_url)
        files_info = filestore.get_files()

        # save path created
        path = files_info.path

        # force delete
        del files_info

        # check if files are gone
        found = False
        for fn in self.test_file_names:
            if os.path.isfile(f"{path}/{fn}"):
                found = True
                break

        self.assertFalse(found)

        pass

if __name__ == '__main__':
    unittest.main()
