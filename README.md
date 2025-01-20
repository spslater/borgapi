# BorgAPI

A helpful wrapper for `borgbackup` to be able to easily use it in python scripts.

**This is not supported use case by the `borg` developers. They only intend for it's use via a CLI.**
Keeping parity with `borg` is the main goal of this api.

## Installation
```
pip install borgapi
```

Requires:
* `borgbackup`: 1.4.0
* `python-dotenv`: 1.0.1

Supports Python 3.9 to 3.13

## Usage
```python
import borgapi

api = borgapi.BorgAPI(defaults={}, options={})

# Initalize new repository
api.init("foo/bar", make_parent_dirs=True)

# Create backup 
result = api.create("foo/bar::backup", "/home", "/mnt/baz", json=True)
print(result['archive']["name"]) # backup
print(result["repository"]["location"]) # foo/bar
```

### BorgAPI Init arguments
```python
class BorgAPI(
    defaults: dict = None,
    options: dict = None,
    log_level: str = "warning",
    log_json: bool = False,
    environ: dict = None,
)
```
* __defaults__: dictionary that has command names as keys and value that is a dict of
  command specific optional arguments
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
* __options__: dictionary that contain the optional arguments (common, exclusion, filesystem, and
  archive) used for every command (when valid). Options that aren't valid for a command will get
  filterd out. For example, `strip_components` will be passed into the `extract` command but not
  the `diff` command.
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
* __log_level__: default log level, can be overriden for a specific comand by passing in another
  level as and keyword argument
* __log_json__: log lines written by logger are formatted as json lines, passed into the
  logging setup
* __environ__: dictionary that contains environmental variables that should be set before running
  any commands. Useful for setting the passphrase or passcommand for the repository or other
  settings like that. See [Environment Variables](#Setting-Environment-Variables) section for
  how to set environmental variables after initalization or what the defaults are.
```python
{
  "BORG_CHECK_I_KNOW_WHAT_I_AM_DOING": "YES",
  "BORG_PASSCOMMAND": "cat ~/.borg/password",
}
```

### Setting Environment Variables
You are able to manage the environment variables used by borg to be able to use different settings
for different repositories.

When initialzing the `BorgAPI` object, you can include a dictionary with the `environ` argument.

The following are the defaults that BorgAPI will always load so that user input does not hold up
the app from progressing.
```ini
BORG_EXIT_CODES=modern,
BORG_PASSPHRASE="",
BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=no,
BORG_RELOCATED_REPO_ACCESS_IS_OK=no,
BORG_CHECK_I_KNOW_WHAT_I_AM_DOING=NO,
BORG_DELETE_I_KNOW_WHAT_I_AM_DOING=NO,
```

There are 3 ways you can set the variables after initialization:
1. `filename`: Path to a file that contains the variables and their values. See the
   [python-dotenv README](https://github.com/theskumar/python-dotenv/blob/master/README.md#file-format)
   for more information.
2. `dictionary`: Dictionary that contains the variable names as keys with their corresponding
   values set.
3. `**kwargs`: Argument names are the variable names and the values are what will be set.

```python
api.set_environ(filename="foo/bar/.env")
api.set_environ(dictionary={"FOO":"BAR", "SPAM":False})
api.set_environ(FOO="BAR", SPAM=False)
```
Only one value will be used if multiple set, `filename` has highest precedence,
followed by `dictionary`, and fallback to `**kwargs`.

If no values are given for any of the three things (ie. calling with no arguments), then the
default behavior for `load_dotenv` from [python-dotenv](https://github.com/theskumar/python-dotenv)
will be used, which is searching for a ".env" file somewhere above in the current file path.

[Environment Variables](https://borgbackup.readthedocs.io/en/stable/usage/general.html#environment-variables)
used by `borgbackup`.

### Removing Environment Variables
If you want to unset a variable so it doesn't get used for another command you can use the
`unset_environ` method. It'll remove any variables passed in from the current environment.
If no variables are passed in, it'll remove the variables set from the last call to `set_environ`.

```python
# Enironment = {}
api.set_environ(dictionary={"FOO":"BAR", "SPAM":False})
# Enironment = {"FOO": "BAR", "SPAM": "False"}
api.unset_environ("FOO")
# Enironment = {"SPAM": "False"}
api.set_environ(BAZ="HAM")
# Enironment = {"SPAM": "False", "BAZ": "HAM"}
api.unset_environ("OTHER")
# Enironment = {"SPAM": "False", "BAZ": "HAM"}
api.unset_environ()
# Enironment = {"SPAM": "False"}
```

## Borg Commands
When using a borg command any of the arguments can be set as keyword arguments.
The argument names are the long option names with dashes turned into underscores.
So the `--storage-quota` argument in `init` gets turned into the keyword argument `storage_quota`.

```python
api.init(
    repository="foor/bar",
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
    "foo/bar::tuesday",
    "friday",
    "foo/bar",
    "/baz",
    **diff_args,
)
```

### Available Borg Commands
* init
* create
* extract
* check
* rename
* list
* diff
* delete
* prune
* compact
* info
* mount
* umount
* key change-passphrase (key_change_passphrase)
* key export (key_export)
* key import (key_import)
* upgrade
* recreate
* immport-tar (immport_tar)
* export-tar (export_tar)
* serve
* config
* with-lock (with_lock)
* break-lock (break_lock)
* benchmark crud (benchmark_crud)

### Command Quirks
Things that were changed from the way the default borg commands work to make things a bit
more manageable.

* __init__
  * `encryption` is an optional argument that defaults to `repokey`
* __config__
  * `borg config` can only change one key at a time
  * `*changes` can either be:
    * `NAME` to get the current value of the key
    * `(NAME, VALUE)` which will change they key
  * Any single string `NAME` values passed to `*change` will be returned as a list with their
    values in the order they were passed, tuple changes will not appear in that list

### Capturing Output
`borg` commands display information different depending on what is asked for.
For example, `create` with the `--list` option writes the file list to the logger.
When the `--log-json` common flag is included it writes it to stderr. The `--stats`
option writes to the logger, like the `--list` option does, but when `--json` is used,
which outputs the stats info as a json object, it gets written to stdout.

If either `json` or `log_json` is set, it'll try to convert the tuple output to json.
If it is unable and there is output that is captured it'll return the plaintext value.
If no output is captured, it returns `None` if expecting a string or `{}` (an empty
dictionary) if expection some kind of JSON output.

If multiple outputs are requested at the same time (like `--stats` and `--list`) the command
will return a dictionary with aptly named keys (`--list` key is "list"). If only one output
is requested than the bare value will be returned, not in a dictionary.

#### Command Returns
Commands not listed return no output (None)
- create
  - list: `--list`, `--log-json`
  - stats: `--stats`, `--json`
- extract
  - list: `--list`, `--log-json`
  - extract: `--stdout`
- list:
  - list: always returns bare value
  - `--log-json`, `--json`, `--json-lines`
- diff:
  - diff: always returns bare value
  - `--log-json`, `--json-lines`
- delete:
  - stats: always returns bare value
  - `--stats`
- prune:
  - list: `--list`, `--log-json`
  - stats: `--stats`, `--log-json`
- compact:
  - returns bare value, when verbose or info is set
  - verbose: `--verbose`, `-v`
  - info: `--info`
- info
  - always returns bare value
- recreate:
  - list: `--list`, `--log-json`
  - stats: `--stats`
- import tar
  - list: `--list`
  - stats: `--stats`, `--json`
- export tar
  - list: `--list`, `--log-json`
  - tar: filename == "-"
- config
  - list: `--list`, `--log-json`
  - changes: single values passed into `*changes`
- benchmark crud
  - always returns bare value

## Roadmap
- Start work on Borg's beta branch again and keeping up with those

## Links
* [PyPi Project](https://pypi.org/project/borgapi)
* [Github](https://github.com/spslater/borgapi)

## Contributing
Help is greatly appreciated. First check if there are any issues open that relate to what you want
to help with. Also feel free to make a pull request with changes / fixes you make.

## License
[MIT License](https://opensource.org/licenses/MIT)
