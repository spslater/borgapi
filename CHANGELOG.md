# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
