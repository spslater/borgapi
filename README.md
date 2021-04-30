# BorgAPI

A helpful wrapper for `borgbackup` to be able to easily use it in python scripts.

## Installation
```
pip install borgapi
```

Requires:
* borgbackup: 1.1.16

## Usage
```python
import borgapi

api = borgapi.BorgAPI(defaults={}, options={})

# Initalize new repository
api.init("/foo/bar", make_parent_dirs=True)

# Create backup 
output = api.create("/foo/bar::backup", "/home", "/mnt/baz", json=True)
print(output["name"]) # backup
print(output["repository"]["location"]) # /foo/bar
```

### BorgAPI Init arguments
```python
class BorgAPI(
    defaults: dict = None,
    options: dict = None,
    log_level: str = 'info',
    log_json: bool = False
)
```
* __defaults__: dictionary that has command names as keys and value that is a dict of command specific optional arguments
```python
{
    "init": {
        "encryption": "repokey-blake2",
        "make_parent_dirs": True,
    },
    "create": {
        "json": True,
    },
}
```
* __options__: dictionary that contain the optional arguments (common, exclusion, filesystem, and archive) used for every command (when valid). Options that aren't valid for a command will get filterd out. For example, `strip_components` will be passed into the `extract` command but not the `diff` command.
```python
{
    "debug": True,
    "log_json": True,
    "exclue_from": "baz/spam.txt",
    "strip_components": 2,
    "sort": True,
    "json_lines": True,
}
```
* __log_level__: defualt log level, can be overriden for a specific comand by passing in another level as and keyword argument
* __log_json__: log lines written by logger are formatted as json lines, passed into the logging setup

## Borg Commands
When using a borg command any of the arguments can be set as keyword arguments.
The argument names are the long option names with dashes turned into underscores.
So the `--storage-quota` argument in `init` gets turned into the keyword argument `storage_quota`.

Examples:
```python
api.init(
    repository="/foor/bar",
    encryption="repokey",
    append_only=True,
    storage_quota="5G",
    make_parent_dirs=True,
    debug=True,
    log_json=True,
)

diff_args = {
    sort: True,
    json_lines: True,
    debug: True,
    exclude_from: "./exclude_patterns.txt",
}

api.diff(
    "/foo/bar::tuesday",
    "friday",
    "/foo/bar",
    "/baz",
    **diff_args,
)
```

### Available Commands
* init
* create
* extract
* check
* rename
* list
* diff
* delete
* prune
* info
* mount
* umount
* key_change_passphrase (key change-passphrase)
* key_export (key export)
* key_import (key import)
* upgrade
* export_tar
* config

### Borg Commands Not Available
* recreate
* serve
* with-lock
* break-lock
* benchmark crud

### Command Quirks
Things that were changed from the way the default borg commands work to make things a bit more manageable.

* __init__
  * `encryption` is an optional argument that defaults to `repokey`

## Roadmap
* Add ability to set environment variables from api (either a function or part of the initalizer or both)
  * https://borgbackup.readthedocs.io/en/stable/usage/general.html#environment-variables
  * Currently requires user to set them beforehand

## Contributing
Help is greatly appreciated. First check if there are any issues open that relate to what you want to help with. 
Also feel free to make a pull request with changes / fixes you make.

## License
[MIT License](https://opensource.org/licenses/MIT)
