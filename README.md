# Runtime Container

Runtime manager that can start modules inside containers or by launching a WASM/Python runtime/interpreter in a separate process (instead of WASM micro-processes).

### Notes

- `script.py` and associated entrypoint in `setup.py` (allows to call some functionality of the package directly from command line (try `package_name cmd1`))
