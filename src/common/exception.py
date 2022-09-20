"""
*TL;DR
Runtime exceptions we handle; Deliver error message and do not cause the runtime to stop
"""
from logzero import logger
class RuntimeException(Exception):
    """Base class for runtime exceptions."""

    def __init__(self, description, data):
        super().__init__(description)
        self.desc = description
        self.data = data
        logger.error(f"{description}: {data}")
        
    def error_msg_payload(self):
        return {"desc": f"Runtime exception: {self.desc}", "data": self.data}

class MissingField(RuntimeException):
    """Required field is missing."""

    def __init__(self, data):
        super().__init__("missing field", data)

class InvalidArgument(RuntimeException):
    """Invalid argument."""

    def __init__(self, arg_name, arg_value):
        super().__init__(
            {"desc": "invalid {}".format(arg_name), "data": arg_value})

class NotDeclaredField(RuntimeException):
    """Field is not acceptable by type."""

    def __init__(self, data):
        super().__init__("non acceptable field", data)
class ProgramFileException(RuntimeException):
    """Error copying/downloading/... a file."""

    def __init__(self, data):
        super().__init__("error getting program file", data)

class LauncherException(RuntimeException):
    """Error instantiating a launcher, creating/starting a module."""

    def __init__(self, data):
        super().__init__("error in launcher", data)
