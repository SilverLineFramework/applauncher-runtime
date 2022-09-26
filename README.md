# Sideload Runtime

A Runtime that sideloads Modules (Modules are a [Silverline Framework](https://github.com/SilverLineFramework) concept). With this runtime, Modules can be started in containers to run standalone python interpreters or WASM runtimes (instead of directly on WASM micro-processes).

The purpose of this runtime is two-fold: (i) allow container/based applications to be managed by Silverline and (2) prototype different aspects of Silverline runtimes.

## Prerequisites

You need to have [Python 3](https://command-not-found.com/python3), [Make](https://command-not-found.com/make), [CURL](https://command-not-found.com/curl) and [sha256sum](https://command-not-found.com/sha256sum) installed. The Makefile creates a [Python virtual environment that deals with installing all Python dependencies](https://github.com/sio/Makefile.venv).

## Quick Start

1. Clone the repository.
2. Edit `conf/settings.yaml` to match your system/preferences (namely the MQTT connection). Here is an example:
```yaml
# logzero log level: CRITICAL (fewer messages), ERROR, WARNING, INFO, DEBUG (more messages)
loglevel: INFO 

# runtime settings
runtime:
  name: aruntime # runtime name
  #uuid: # leave blank to generate a new uuid; or set a fixed uuid value
  reg_attempts: 0 # 0 = infinite; keeps trying to register
  reg_timeout_seconds: 5 # interval between register attempts
  max_nmodules: 100 # maximum number of modules we support
  realm: realm # realm topic used

# mqtt settings (NOTE: username and password in conf/.secrets.yaml)
mqtt:
  host: broker.com # broker host
  port: 1883 # broker port
  ssl: true # use ssl connection (true/false)

# where/how we keep program files
repository:
  url: https://filestore-host/store # base url where to get download program files

# launcher config; what starts modules 
launcher:
  pipe_stdout: true # stdout/err piped to pubsub (true/false)
```

> **Note**: If your MQTT broker requires a password:
>
> 1. Copy `conf/.secrets-example.yaml` to `conf/.secrets.yaml`
>
> 2. Edit `conf/.secrets.yaml` with the username and password. The format is as follows (do not delete the `dynaconf_merge: true` configuration)
>
>    ```
>    dynaconf_merge: true # merge with sonf/settings.yaml (required)
>    mqtt:
>      username: ausername
>      password: apassword
>    ```

3. Start the runtime using the `run` Makefile target:
`make run`

> You can install the dependencies manually and run the program directly with Python 3 if you do not want to install Make.
 
## Application Settings

User-facing settings are defined in `conf/settings.yaml`. This is what you will want to edit most of the time. Internal settings are kept in the `conf/.appsettings.yaml`, which will be more relevant if you wish to change internal runtime behavior. 

Most settings are related to how modules are started using a **module launcher**. A module launcher is the implementation of a particular way of starting modules. For example, a module launcher can start python programs inside a container and instantiate
a docker client to do so. Different launchers can be implemented. A module launcher factory (LauncherContext) instantiates launchers based on `conf/.appsettings.yaml`.

## Container Images for Launchers

Launchers use custom images to startup modules. The `containers` folders has the build files for these images. The images created here are then used in the `launcher.docker.image` setting for the corresponding laucher config in `conf/.appsettings.yaml`.
