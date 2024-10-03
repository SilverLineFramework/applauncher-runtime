"""
*TL;DR
Some utils: instantiate classes from settings, singleton metaclass
"""
import importlib

from .config import settings
from .exception import LauncherException

class ClassUtils:
    """ Class utils; import class from settings key """
    @staticmethod
    def class_instance_from_settings_class_path(settings_class_path_key, **kwargs):
        """
            Return a class instance from settings key; value in the form: module.submodule.Class
            Arguments dictionary passed to class constructor
        """
        class_path = settings.get(settings_class_path_key, None)
        if not class_path:
            raise LauncherException(f"No settings found for launcher {settings_class_path_key}")

        (launcher_module, launcher_class) = class_path.rsplit('.', 1)
        try:
            the_class = getattr(importlib.import_module(launcher_module), launcher_class)
        except ModuleNotFoundError as import_exception:
            raise LauncherException(f"No launcher class found for {class_path}") from import_exception
        return the_class(**kwargs)
