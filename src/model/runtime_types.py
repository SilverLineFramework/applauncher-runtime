"""
*TL;DR
Utility types used in runtime messages and models
"""

from enum import Enum
class Result(str, Enum):
    """Result ok/error enum."""
    ok = 'ok'
    err = 'error'

class Action(str, Enum):
    """Action create/delete enum."""
    create = 'create'
    delete = 'delete'

class MessageType(str, Enum):
    """Message type (runtime/module) enum."""
    rt = 'runtime'
    mod = 'module'

class FileTypes(str, Enum):
    """File types enum."""
    WA = 'WASM'
    PY = 'PYTHON'

class APIs(str, Enum):
    """Apis enum."""
    python3 = 'python:python3'
    wasi_preview_1 = 'wasi:snapshot_preview1'

class RuntimeLauncherTypes(str, Enum):
    """Runtime/Module launcher types enum."""
    module_container = 'module-container'
    python_native = 'python-native'
