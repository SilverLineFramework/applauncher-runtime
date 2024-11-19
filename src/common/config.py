
from dynaconf import Dynaconf, Validator
import uuid
import os

settings = Dynaconf(
    settings_files=["settings.yaml", ".secrets.yaml", ".appsettings.yaml"],
    validators=[

        # must be version 0.1 or higher
        Validator("version", default=0, gte=0.1),

        # default log level and allowed values
        Validator("loglevel", default="INFO", is_in=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
        
        # runtime required settings
        Validator("runtime.name", "runtime.uuid", "runtime.runtime_type", "runtime.apis", must_exist=True),
        Validator("runtime.namespace", default='public'),
        Validator("runtime.reg_attempts", default=1),
        Validator("runtime.reg_timeout_seconds", default=5),
        Validator("runtime.reg_fail_error", default=True),
        Validator("runtime.max_nmodules", default=100),
        Validator("runtime.realm", default="realm"),
        Validator("runtime.is_orchestration_runtime", default=False),
        Validator("runtime.tags", default=[]),

        # gen runtime uuid default value (if empty)
        Validator("runtime.uuid", default=str(uuid.uuid4())),

        # mqtt required settings
        Validator("mqtt.host", "mqtt.port", "mqtt.ssl", must_exist=True),

        # topic list is required (no check on particular topic vaules due to template substitution)
        Validator("topics", must_exist=True),
        Validator("topics.runtimes", must_exist=True),
        Validator("topics.modules", must_exist=True),
        Validator("topics.mio", must_exist=True),

        # repository required settings
        Validator("repository.class", must_exist=True),

        # launcher required settings
        Validator("launcher.apis", must_exist=True),

        # username and password are an empty string by default
        Validator("mqtt.password", default=""),
        Validator("mqtt.username", default=""),

        Validator("docker.force_container_name", default=False),
    ],
)
