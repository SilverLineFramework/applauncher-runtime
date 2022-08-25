import unittest

from launcher.python_launcher import PythonLauncher
from launcher import LauncherContext
from model import Module
from common import settings

class TestLauncher(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # instantiate a python module for testing
        self.module = Module(name='test_mod', filename='arena/py/pytestenv', filetype='PY')
        
    def test_python_launcher(self):
        # setup launcher
        mod_launcher = LauncherContext.get_launcher(self.module)
        print(mod_launcher)
        mod_launcher.start_module()
        pass

if __name__ == '__main__':
    unittest.main()
