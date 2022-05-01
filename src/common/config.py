
from dynaconf import Dynaconf, Validator
import uuid

settings = Dynaconf(
    settings_files=['settings.yaml', '.secrets.yaml'],
    validators=[
        # runtime required settings
        Validator('runtime.name', 'runtime.uuid', 'runtime.runtime_type', 'runtime.apis', 'runtime.reg_attempts', 'runtime.reg_timeout_seconds', 'runtime.max_nmodules', 'runtime.realm', must_exist=True),

        # gen runtime uuid default value (if empty)
        Validator("runtime.uuid", default=str(uuid.uuid4())),

        # mqtt required settings
        Validator('mqtt.host', 'mqtt.port', 'mqtt.ssl', must_exist=True),

        # topic list is required (can't check particular topics due to template substitution ?)
        Validator('topics', must_exist=True),

        # store required settings
        Validator('store.url', must_exist=True),

        # laucher required settings
        Validator('launcher.class', 'launcher.apis', 'launcher.args', must_exist=True),
    ],
)
