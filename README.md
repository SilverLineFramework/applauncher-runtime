# Runtime Container

Runtime manager that can start modules inside containers, which can be standlone python interpreters or WASM runtimes (instead of directly on WASM micro-processes).

### Notes

- `script.py` and associated entrypoint in `setup.py` (allows to call some functionality of the package directly from command line (try `package_name cmd1`))
