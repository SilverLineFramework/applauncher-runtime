"""Message definitions."""

import uuid
import json

from mqtt.mqtt_msg import MQTTMessage
from common.config import settings

class Result:
    """Result ok/error enum."""

    ok = 'ok'
    err = 'error'

class Action:
    """Action create/delete enum."""

    create = 'create'
    delete = 'delete'

class Type:
    """Type (runtime/module) enum."""
    rt = 'runtime'
    mod = 'module'

class FileTypes:
    """File types enum."""
    WA = 'WASM'
    PY = 'PYTHON'

class APIs:
    """Apis enum."""

    python3 = 'python:python3'
    wasi_preview_1 = 'wasi:snapshot_preview1'

class LauncherTypes:
    """Module launcher types enum."""

    module_container = 'module-container'
    python_native = 'python-native'

def __convert_str_attrs(d):
    """Convert JSON-encoded string attributes into proper objects."""
    convert_keys = ['apis', 'args', 'env', 'channels', 'peripherals', "aot_target"]
    # convert array attributes saved as strings into objects
    for key in convert_keys:
        try:
            attr_str = d[key].replace("'", '"')
            d[key] = json.loads(attr_str)
        except Exception as _:
            pass

def ErrorMsg(data):
    """Error message to stderr topic."""
    return MQTTMessage(settings.topics.stderr, data)

def ResponseMsg(topic, src_uuid, details, result=Result.ok, convert=False):
    """Response."""
    if convert:
        __convert_str_attrs(details)
    return MQTTMessage(topic, {
        "object_id": str(src_uuid), "type": "runtime_resp",
        "data": {"result": result, "details": details}
    })

def RequestMsg(topic, action, data, convert=True):
    """Request."""
    if convert:
        __convert_str_attrs(data)
    return MQTTMessage(topic, {
        "object_id": str(uuid.uuid4()), "action": action, "type": "runtime_req",
        "data": data
    })
