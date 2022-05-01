# General Information

# Notes

- `script.py` and associated entrypoint in `setup.py` (allows to call some functionality of the package directly from command line (try `package_name cmd1`))

## Usage

- Rename directory `src/package_name`
- Edit `setupy.py`: replace dummy data with real data.
- Add your source. a) Either to [`core.py`](src/package_name/core.py) or b) to your own separate file(s).
    - a) simplifies importing your module
    - b) is more flexible but you have to take care of importability yourself.
