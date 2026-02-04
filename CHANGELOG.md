# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2026-02-04
### Changed
- `pyproject.toml` now explicitly lists the package in the `[tool.setuptools]` section
  instead of using the find / where sytax

## [0.7.0] - 2025-01-20
### Added
- Borg command `recreate` and `import-tar` [#24]
- Async class! Now you can view output logs while the command is running and not only 
  when it has completed. This makes the `--progress` flag not useless. [#21]
- Support for Python version 3.12 and 3.13
- Add `environ` argument to the `BorgAPI` constructor
- Load default environmental variables to prevent the api from freezing while waiting for
  user input. They won't be overriden if they are already set. See README for list of 
  variables that get set and their defaults. [#20]

### Changed
- Borg version bumped to 1.4.0
- Changed the version requirements for `borgbackup` and `python-dotenv` to use compatible
  release clause (`~=`) instead of a version matching (`==`) clause. This should allow any
  security patches published to still work while any minor chagnes will need to be verified. 
- Using `ruff` to lint and format now. Previously used `pylint` to lint and `black` and
  `isort` to format.

### Removed
- No longer support Python 3.8 because borgbackup no longer supports that version.

## [0.6.1] - 2023-03-27
### Changed
- Borg version bumped to 1.2.4
- Dotenv version bumped to 1.0.0 in "requirements.txt"

## [0.6.0] - 2023-03-13
### Added
- Borg command `compact`

### Changed
- Borg version bumped to 1.2.3
- Dotenv version bumped to 1.0.0
- Dropped support for Python 3.6 and 3.7
- Added support for Python 3.11
- Default log level is "warning" instead of "info"
- Capturing json output uses Borgs JsonFormatter for the logger
- Log level is passed for each command so individual command calls can accurately refelct wanted
  output, before if `log_json` was used, it ignored log level

### Fixed
- Mounting / Unmounting tests failing due to OS taking some time, added a longer sleep to prevent
  them from failing
- `fuse` in the optional install requirements was the incorrect name of the package,
  changed to `llfuse`
- Readme reflects acutally current return values for commands, had still referenced an old style

## [0.5.0] - 2021-06-17
### Changed
- Commands not returns a single value
  - If multiple values are captured, a `dict` is returned with relevant key names
  - Single value is returned by itself
  - No captured value returns `None`

### Fixed
- Missing benchmark test added back in

## [0.4.0] - 2021-06-11
### Changed
- Type hint for command returns changed to custom type hint `BorgRunOutput` which is a tuple
  `Union[str, dict, None]` for stdout and stderr capture

### Fixed
- `change`
  - `changes` argument now positional magic variable. (`*changes`)
  - Passing in strings to get the values returns a list
  - Passing in tuples to set the values returns None
- `import` and `export`:
  - Appends `path` to end of args instead of trying to extend because only one path can be passed
- `benchmark_crud`:
  - Command is now added as two seperate words instead of one
    (`"benchmark crud"` -> `["benchmark", "crud"]`)
- `ExclusionOptions`:
  - `pattern` now processed as a list

## [0.3.1] - 2021-06-09
### Changed
- Commands now return captured `stdout` and `stderr` instead of just `stdout`

### Fixed
- `borg` removes the first value from the args list. The list being passed in started with the
  command name (eg `init`, `create`, `list`) so that was getting removed. Added `borgapi` as the
  first argument for it to get removed when the command is called now.

## [0.2.1] - 2021-05-15
### Added
- Borg commands `serve`, `with-lock`, `break-lock`, and `benchmark crud` as
  `serve`, `with_lock`, `break_lock`, and `benchmark_crud` respectivly.

## [0.2.1-alpha.1] - 2021-05-15
### Added
- Added missing options to the following commands:
  - prune: `keep_last`
  - mount: `o`
- Added missing options to the following `Options` dataclasses:
  - CommonOptions: `debug_topic`

### Changed
- Added `python-dotenv` to the Installation section in the README
- Add warning at top of README file saying how this is not how the borg developers intended use.
- Add roadmap items to the README
- Add `config` to the "Command Quirks" section of readme

### Fixed
- `__post_init__` was not being called by the `__init__` function, moved logic from `__post_init__`
  into `__init__`

## [0.2.0] - 2021-05-10
### Added
- Loading environment variables using
  [python-dotenv v0.17.1](https://github.com/theskumar/python-dotenv/releases/tag/v0.17.1)
- Info on how to set and unset environment variables

### Changed
- Formated the README to have shorter line lenghts, no changes in display
- Removed the Roadmap item for loading environment variables

## [0.1.2-alpha.1] - 2021-05-10
### Added
- Sample files to help with understanding different setttings

### Changed
- Moved the `.env.sample` file into the sample folder with the other added sample files

## [0.1.1] - 2021-05-10
### Added
- Links in the README to the PyPi project and Github repository

### Changed
- Homepage url for the project from selfhosted Gitea site to github.
- License to MIT License from [Anti-Capitalist Software License](https://anticapitalist.software/)
