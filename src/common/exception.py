"""
*TL;DR
Runtime exceptions we handle; Deliver error message and do not cause the runtime to stop
"""

class RuntimeException(Exception):
    """Base class for runtime exceptions."""

    def __init__(self, description, data):
        super().__init__()
        self.desc = description
        self.data = data

class MissingField(RuntimeException):
    """Required field is missing."""

    def __init__(self, data):
        super().__init__("missing field", data)

class ProgramFileException(RuntimeException):
    """Error copying/downloading/... a file."""

    def __init__(self, data):
        super().__init__("error getting program file", data)

class LauncherException(RuntimeException):
    """Error instantiating a launcher, creating/starting a module."""

    def __init__(self, data):
        super().__init__("error in launcher", data)
