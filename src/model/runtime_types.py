"""
*TL;DR
Utility types used in runtime messages and models
"""
class Result():
    """Result ok/error enum."""
    ok = 'ok'
    err = 'error'

class Action():
    """Action create/delete enum."""
    create = 'create'
    delete = 'delete'
    update = 'update'

class MessageType():
    """Message type (runtime/module) enum."""
    rt = 'runtime'
    mod = 'module'

class FileTypes():
    """File types enum."""
    WA = 'WASM'
    PY = 'PYTHON'

class APIs():
    """Apis enum."""
    python3 = 'python:python3'
    wasi_preview_1 = 'wasi:snapshot_preview1'

class RuntimeLauncherTypes():
    """Runtime/Module launcher types enum."""
    module_container = 'module-container'
    python_native = 'python-native'
