# AppLauncher Runtime — Detailed Specification

## Purpose

AppLauncher Runtime is a Python service that acts as a **compute node** in the [Silverline Framework](https://github.com/SilverLineFramework) — a system for distributed execution of programs across heterogeneous runtimes. Its two roles are:

1. **Module lifecycle management** — receives create/delete requests from an orchestration layer and launches/stops programs in isolated Docker containers.
2. **Prototyping vehicle** — serves as a reference implementation and testbed for different Silverline runtime behaviors (containerised workloads vs. native, Python vs. WASM).

---

## System Context

```
┌─────────────────────────────────────┐
│  Silverline Orchestration Layer     │
│  (ARENA, or other Silverline-aware  │
│   orchestrator)                     │
└──────────────┬──────────────────────┘
               │  MQTT
       ┌───────▼──────────┐
       │   MQTT Broker    │
       └───────┬──────────┘
               │
       ┌───────▼──────────────────────────────────────┐
       │  AppLauncher Runtime  (this service)         │
       │                                              │
       │  MQTTListner ──► RuntimeMngr                 │
       │                      │                       │
       │              LauncherContext (factory)        │
       │                      │                       │
       │              PythonLauncher                  │
       │                      │                       │
       │              DockerClient ──► [Container]    │
       │                                   │          │
       │              PubsubStreamer ◄──────┘          │
       └──────────────────────────────────────────────┘
```

---

## MQTT Topic Scheme

All communication goes through a topic hierarchy. Variable parts are resolved at startup or per-module:

| Topic pattern | Purpose |
|---|---|
| `realm/g/<namespace>/p/<runtime-uuid>` | Runtime registration, keepalives, errors |
| `realm/s/+/+/p/+/+` | Module control — runtime subscribes to all (wildcard) |
| `realm/s/<namespace>/<scene>/p/<module-uuid>` | Module I/O base (MIO) |
| `realm/s/<namespace>/<scene>/p/<module-uuid>/-/stdout` | Module stdout stream |
| `realm/s/<namespace>/<scene>/p/<module-uuid>/-/stdin` | Module stdin stream |
| `realm/s/<namespace>/<scene>/p/<module-uuid>/-/stderr` | Module stderr stream |

The `-/` prefix on I/O topics signals these messages do not conform to the standard Silverline message format.

---

## Message Format

All control messages are JSON objects with this envelope:

```json
{
  "object_id": "<uuid>",
  "action": "create | delete | update",
  "type": "req | resp | runtime | module",
  "from": "<sender-uuid>",
  "data": { ... }
}
```

`stdin/stdout/stderr` messages are raw strings (no envelope).

---

## Runtime Lifecycle

### 1. Startup

- Load layered configuration (Dynaconf: `settings.yaml` + `.appsettings.yaml` + per-env overrides).
- Create `RuntimeMngr` (holds runtime state, module registry).
- Create `MQTTListner` (paho.mqtt wrapper), connect to broker.
- Set MQTT last-will to a runtime delete message (published by the broker if the runtime crashes without a clean disconnect).

### 2. Registration

- On MQTT connect, subscribe to the runtimes topic and begin sending periodic `create` request messages (registration).
- Registration can be configured to: skip (`reg_attempts: -1`), retry indefinitely (`reg_attempts: 0`), or retry N times.
- On receiving an `ok` response from the orchestrator, registration is complete.
- After registration: unsubscribe from runtimes topic, subscribe to the modules wildcard topic, start the keepalive thread.

### 3. Running

The runtime sits idle, processing two categories of MQTT events:

- **Module create requests** → launch a module.
- **Module delete requests** → stop a module.

### 4. Keepalive

A background thread publishes an `update` message to the runtimes topic at a configurable interval (`ka_interval_sec`). The payload includes the runtime's identity attributes plus a `children` array containing stats for each running module.

### 5. Shutdown

On process exit (`atexit` hook):
- Signal keepalive thread to stop.
- Stop all running containers.
- Publish the last-will message explicitly (runtime delete request).

---

## Module Lifecycle

### Create

1. Orchestrator publishes a `create` request to `realm/s/<ns>/<scene>/p/<runtime-uuid>/<anything>`.
2. `RuntimeMngr.control()` receives it, validates `parent` matches this runtime's UUID or name.
3. A `Module` object is instantiated (validates required fields: `uuid`, `name`, `file`, `filetype`, `parent`).
4. `LauncherContext.get_launcher_for_module()` looks up `launcher.<FILETYPE>` in config and instantiates the appropriate `ModuleLauncher` class via reflection.
5. `PythonLauncher.start_module()`:
   - Writes `.arena_mqtt_auth` token file (MQTT credentials for arena-py inside the container).
   - Calls `FileStoreBuilder.from_module_data()` to resolve file URLs from `repository.url + module.location + module.file`.
   - Downloads all files listed by the HTTP directory index into a temp folder.
   - Starts a Docker container (`slruntime-python-runner` image) with:
     - The temp folder mounted to `/usr/src/app`.
     - `PROGRAM_OBJECT_ID=<module-uuid>` environment variable injected.
     - Module's `env` and `args` passed through.
     - stdin/stdout/stderr attached to a socket.
   - A `PubsubStreamer` bridges that socket to the module's MIO MQTT topics (reads Docker's multiplexed stream format).
6. `RuntimeMngr` publishes a confirmation response to the module's MIO topic.

### Delete

1. Orchestrator publishes a `delete` request.
2. `RuntimeMngr` saves the request as a "pending delete" message.
3. Calls `DockerClient.stop()` on the container.
4. Docker container exits → exit callback fires → `__module_exit()` removes the module from the registry and publishes the pending delete confirmation.

---

## Key Components

### `RuntimeMngr` (`src/runtime/runtime_mngr.py`)

The central coordinator. Implements `PubsubHandler` (called by `MQTTListner` on events). Holds:
- `__modules: Dict[str, MngrModule]` — all running modules indexed by UUID.
- Registration/keepalive threads.
- Pending delete message buffer.

### `MQTTListner` (`src/pubsub/listner.py`)

Wraps paho-mqtt. Manages subscriptions, publishes, JSON encoding/decoding, and error publishing. Delivers decoded messages to registered handlers.

### `LauncherContext` (`src/launcher/launcher.py`)

Factory. Reads `launcher.<FILETYPE>` config, instantiates a `ModuleLauncher` subclass by its fully-qualified class path (e.g., `launcher.python_launcher.PythonLauncher`).

### `PythonLauncher` (`src/launcher/python_launcher.py`)

Implements `ModuleLauncher` for `filetype=PY`. Wires together `FileStoreBuilder` (file download), `DockerClient` (container management), and `PubsubStreamer` (I/O bridging).

### `DockerClient` (`src/launcher/docker_client.py`)

Thin wrapper around the Docker Python SDK. Starts containers with stdin/stdout/stderr attached to a socket, monitors for exit, collects CPU/memory/network stats.

### `PubsubStreamer` (`src/pubsub/pubsub_streamer.py`)

Runs two directions concurrently:
- **Output thread**: reads Docker's multiplexed byte stream (8-byte header + payload), routes to `stdout` or `stderr` MQTT topics.
- **Input handler**: subscribes to the `stdin` MQTT topic, writes received messages to the container's stdin socket.

### `FileStoreBuilder` (`src/program_files/filestore_builder.py`)

Downloads program files from an HTTP server. Parses HTML directory index pages using BeautifulSoup, recursively follows subdirectories. Also injects additional files (auth tokens) into the working directory before mounting.

### `Module` / `Runtime` (models)

Dictionary subclasses with typed properties. `Module` tracks `uuid`, `name`, `file`, `filetype`, `parent`, `location`, `scene`, `env`, `args`, `channels`, `apis`, `resources`, `peripherals`. `Runtime` tracks its own identity attributes and topic configuration.

---

## Configuration

Uses **Dynaconf** with layered files merged at startup:

| File | Who edits | Content |
|---|---|---|
| `config/settings.yaml` | Users | MQTT broker, runtime name, log level, repository URL |
| `config/.appsettings.yaml` | Developers | Launcher classes, topic templates, repository class |
| `config/<env>/settings.yaml` | Deployers | Per-environment overrides |
| `config/<env>/.secrets.yaml` | Deployers | MQTT username/password |

### Key settings

| Key | Default | Description |
|---|---|---|
| `runtime.name` | `containerized-runtime` | Human-readable runtime name |
| `runtime.uuid` | auto-generated | Fixed UUID if set; new UUID each run if omitted |
| `runtime.reg_attempts` | `-1` (skip) | Registration retries |
| `runtime.max_nmodules` | `100` | Max concurrent modules |
| `runtime.ka_interval_sec` | `60` | Keepalive interval (seconds) |
| `launcher.pipe_stdout` | `true` | Bridge container stdout/stderr to MQTT |
| `launcher.PY.docker.image` | `slframework/slruntime-python-runner` | Container image for Python modules |
| `repository.url` | `https://localhost/store` | Base URL for program file downloads |

---

## Supported Module File Types

| `filetype` | Launcher | Container Image | Notes |
|---|---|---|---|
| `PY` | `PythonLauncher` | `slruntime-python-runner` | Runs arena-py programs; entrypoint installs `requirements.txt` then runs `python3 -u <file> [args]` |
| `WA` | `WasmLauncher` | `python` (placeholder) | Referenced in config; not implemented in this codebase |

---

## Container Images

**`slruntime-python-runner`** (stable):
- Base: `python:3.12.5`
- Installs: `arena-py` (pinned version from `VERSION` file) + requirements
- Entrypoint: installs `requirements.txt` if present, then `python3 -u <args>`

**`slruntime-python-runner-repo-head`** (development):
- Same as above but installs `arena-py` from the repository HEAD (latest unreleased version)

---

## Module Stats (reported in keepalives)

| Field | Unit |
|---|---|
| `cpu_usage_percent` | % |
| `mem_usage` | bytes |
| `network_rx_mb` / `network_tx_mb` | MB |
| `network_rx_pkts` / `network_tx_pkts` | packet count |

---

## Extensibility Points

- **New launchers**: implement `ModuleLauncher` protocol (`start_module`, `stop_module`, `get_stats`), add `launcher.<FILETYPE>.class` to `.appsettings.yaml`.
- **New repositories**: implement `ProgramFilesBuilder`, add `repository.class` to `.appsettings.yaml`.
- **QoS**: `DockerClient` implements a `QoSParams` protocol stub for future per-module CPU/memory limits (currently hardcoded to 25% of 1 CPU).

---

## Deployment

- **Interactive mode** (default): blocks waiting for `Q` + Enter on stdin.
- **Daemon mode** (`--daemon`): blocks forever via `Event().wait()`, suitable for systemd/Docker.
- **Docker container**: a top-level `Dockerfile` containerises the runtime itself.
- **CI/CD**: GitHub Actions with release-please for automated versioning and changelog.
