"""Run Borg Backups"""

import logging
import os
import sys
from io import BytesIO, StringIO, TextIOWrapper
from json import decoder, loads
from typing import Callable, Dict, List, Optional, Tuple, Union

import borg.archive
import borg.archiver
import borg.helpers
import borg.repository
from dotenv import dotenv_values, load_dotenv

from .options import (
    ArchiveInput,
    ArchiveOutput,
    ArchivePattern,
    CommandOptions,
    CommonOptions,
    ExclusionInput,
    ExclusionOptions,
    ExclusionOutput,
    FilesystemOptions,
    OptionsBase,
)

__all__ = ["BorgAPI"]

BorgRunOutput = Dict[str, Union[str, list, dict, None]]


class OutputCapture:
    """Capture stdout and stderr by redirecting to inmemory streams

    :param raw: Expecting raw bytes from stdout and stderr
    :type raw: bool
    """

    def __init__(self, raw: bool = False):
        self.raw = raw
        self._init_stdout(raw)
        self._init_stderr()

        self.formatter = logging.Formatter("%(message)s")
        self._init_list_capture()
        self._init_stats_capture()

    def _init_stdout(self, raw: bool):
        self.stdout = TextIOWrapper(BytesIO()) if raw else StringIO()
        self.stdout_original = sys.stdout
        sys.stdout = self.stdout

    def _init_stderr(self):
        self.stderr = StringIO()
        self.stderr_original = sys.stderr
        sys.stderr = self.stderr

    def _init_list_capture(self):
        self.list_handler = logging.StreamHandler(StringIO())
        self.list_handler.setFormatter(self.formatter)
        self.list_handler.setLevel("INFO")

        self.list_logger = logging.getLogger("borg.output.list")
        self.list_logger.addHandler(self.list_handler)

    def _init_stats_capture(self):
        self.stats_handler = logging.StreamHandler(StringIO())
        self.stats_handler.setFormatter(self.formatter)
        self.stats_handler.setLevel("INFO")

        self.stats_logger = logging.getLogger("borg.output.stats")
        self.stats_logger.addHandler(self.stats_handler)

    # pylint: disable=no-member
    def getvalues(self) -> Union[str, bytes]:
        """Get the captured values from the redirected stdout and stderr

        :return: Redirected values from stdout and stderr
        :rtype: Union[str, bytes]
        """
        stdout_value = stderr_value = None
        if self.raw:
            stdout_value = self.stdout.buffer.getvalue()
        else:
            stdout_value = self.stdout.getvalue().strip()
        stderr_value = self.stderr.getvalue().strip()

        list_value = self.list_handler.stream.getvalue()
        stats_value = self.stats_handler.stream.getvalue()

        return {
            "stdout": stdout_value,
            "stderr": stderr_value,
            "list": list_value,
            "stats": stats_value,
        }

    def close(self):
        """Close the underlying IO streams and reset stdout and stderr"""
        try:
            self.stdout.close()
            self.stderr.close()
            self.list_handler.stream.close()
            self.list_logger.removeHandler(self.list_handler)
            self.stats_handler.stream.close()
            self.stats_logger.removeHandler(self.stats_handler)
        finally:
            sys.stdout = self.stdout_original
            sys.stderr = self.stderr_original


# pylint: disable=too-many-public-methods
class BorgAPI:
    """Automate borg in code"""

    # pylint: disable=too-many-arguments,not-callable
    def __init__(
        self,
        defaults: dict = None,
        options: dict = None,
        log_level: str = "info",
        log_json: bool = False,
    ):
        self.options = options or {}
        self.optionals = CommandOptions(defaults)
        self.archiver = borg.archiver.Archiver()
        self._previous_dotenv = []
        self._setup_logging(log_level, log_json)

    def _setup_logging(self, log_level: str = "info", log_json: bool = False):
        self.logger_setup = False
        self.archiver.log_json = log_json or self.options.get("log_json", False)
        borg.archiver.setup_logging(level=log_level, is_serve=False, json=log_json)
        self.original_stdout = sys.stdout
        logging.getLogger("borgapi")
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _loads_json_lines(string: str) -> Union[dict, str, None]:
        result = None
        try:
            result = loads(string)
        except decoder.JSONDecodeError:
            clean = f'[{",".join(string.splitlines())}]'
            try:
                result = loads(clean)
            except decoder.JSONDecodeError:
                result = string or None
        return result

    @staticmethod
    def _build_result(*results: Tuple[str, Union[str, list, dict, None]]) -> dict:
        result = {}
        for name, value in results:
            if value:
                result[name] = value
        return result

    # pylint: disable=no-member
    def _run(
        self,
        arg_list: List,
        func: Callable,
        raw_bytes: bool = False,
    ) -> BorgRunOutput:
        self._logger.debug("%s: %s", func.__name__, arg_list)
        arg_list.insert(0, "borgapi")
        args = self.archiver.get_args(arg_list, os.environ.get("SSH_ORIGINAL_COMMAND"))

        prev_json = self.archiver.log_json
        log_json = getattr(args, "log_json", prev_json)
        self.archiver.log_json = log_json

        capture = OutputCapture(raw_bytes)
        try:
            func(args)
        except Exception as e:
            self._logger.error(e)
            raise e
        else:
            capture_result = capture.getvalues()
        finally:
            capture.close()

        self.archiver.log_json = prev_json

        return capture_result

    def _get_option(self, value: dict, options_class: OptionsBase) -> OptionsBase:
        args = {**self.options, **(value or {})}
        return options_class(**args)

    def _get_option_list(self, value: dict, options_class: OptionsBase) -> List:
        option = self._get_option(value, options_class)
        return option.parse()

    def set_environ(
        self,
        filename: str = None,
        dictionary: dict = None,
        **kwargs: Union[bool, str, int],
    ) -> None:
        """Load environment variables from file

        If nothing is provided, load_dotenv's default value will be used.

        :param filename: path to environment file, defaults to None
        :type filename: str, optional
        :param dictionary: dictionary of environment variables to load, defaults to None
        :type dictionary: dict, optional
        :param **kwargs: Environment variables and their values as named args
        :type **kwargs: Union[bool, str, int]
        """
        variables = {}
        if filename:
            self._logger.debug("Loading environment variables from %s", filename)
            variables = dotenv_values(filename)
        elif dictionary or kwargs:
            self._logger.debug("Loading dictionary with data: %s", variables)
            variables = dictionary or kwargs
        else:
            self._logger.debug('Looking for ".env" file to load variables from')
            variables = dotenv_values()

        self._previous_dotenv = variables.keys()

        config = StringIO()
        for key, value in variables.items():
            config.write(f"{key}={value}\n")
        config.seek(0)
        load_dotenv(stream=config, override=True)
        config.close()

    def unset_environ(
        self,
        *variable: Optional[str],
    ) -> None:
        """Remove variables from the environment

        If no variable is provided the values set from the previous call to `set_environ`
            will be removed.

        :param *variable: variable names to remove
        :type *variable: Optional[str]
        """
        variables = [k for k in variable if k in os.environ] or [
            k for k in self._previous_dotenv if k in os.environ
        ]
        for var in variables:
            del os.environ[var]

    def init(
        self,
        repository: str,
        encryption: str = "repokey",
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Initialize an empty repository. A repository is a filesystem directory
        containing the deduplicated data from zero or more archives.

        :param repository: repository to create
        :type repository: str
        :param encryption: select encryption key mode; defaults to "repokey"
        :type encryption: str, optional
        :param **options: optional arguments specific to `init` and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            json dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("init")
        arg_list.extend(["--encryption", encryption])
        arg_list.extend(self.optionals.to_list("init", options))
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_init)

    def create(
        self,
        archive: str,
        *paths: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Create a backup archive containing all files found while recursively
        traversing all paths specified.

        :param archive: name of archive to create (must be also a valid directory name)
        :type archive: str
        :param *paths: paths to archive
        :type *paths: str
        :param **options: optional arguments specific to `create` as well as exclusion,
            filesysem, archive, and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        create_options = self.optionals.get("create", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("create")
        arg_list.extend(create_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionInput))
        arg_list.extend(self._get_option_list(options, FilesystemOptions))
        arg_list.extend(self._get_option_list(options, ArchiveInput))
        arg_list.append(archive)
        arg_list.extend(paths)

        output = self._run(arg_list, self.archiver.do_create)

        stats_result = list_result = None

        if create_options.stats and not create_options.json:
            stats_result = output["stats"]
        elif create_options.json:
            stats_result = self._loads_json_lines(output["stdout"])

        if create_options.list and not common_options.log_json:
            list_result = output["list"]
        elif create_options.list and common_options.log_json:
            list_result = self._loads_json_lines(output["stderr"])

        return self._build_result(
            ("stats", stats_result),
            ("list", list_result),
        )

    def extract(
        self,
        archive: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Extract the contents of an archive.

        :param archive: archive to extract
        :type archive: str
        :param *paths: paths to archive
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `extract` as well as exclusion
            and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        extract_options = self.optionals.get("extract", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("extract")
        arg_list.extend(extract_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(archive)
        arg_list.extend(paths)

        raw_bytes = options.get("stdout", False)
        output = self._run(arg_list, self.archiver.do_extract, raw_bytes=raw_bytes)

        list_result = extract_result = None
        if extract_options.list and not common_options.log_json:
            list_result = output["list"] or None
        elif extract_options.list and common_options.log_json:
            list_result = self._loads_json_lines(output["list"]) or None

        if extract_options.stdout:
            extract_result = output["stdout"]

        return self._build_result(
            ("list", list_result),
            ("extract", extract_result)
        )

    def check(
        self,
        *repository_or_archive: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Verify the consistency of a repository and the corresponding archives.

        :param *repository_or_archive: repository or archive to check consistency of
        :type *repository_or_archive: str
        :param **options: optional arguments specific to `check` as well as archive
            and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("check")
        arg_list.extend(self.optionals.to_list("check", options))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(repository_or_archive)

        return self._run(arg_list, self.archiver.do_check)

    def rename(
        self,
        archive: str,
        newname: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Rename an archive in the repository.

        :param archive: archive to rename
        :type archive: str
        :param newname: the new archive name to use
        :type newname: str
        :param **options: optional arguments specific to `rename` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("rename")
        arg_list.append(archive)
        arg_list.append(newname)

        return self._run(arg_list, self.archiver.do_rename)

    # pylint: disable=redefined-builtin
    def list(
        self,
        repository_or_archive: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """List the contents of a repository or an archive.

        :param repository_or_archive: repository or archive to list contents of
        :type repository_or_archive: str
        :param *paths: paths to list; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `list` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        list_options = self.optionals.get("list", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("list")
        arg_list.extend(list_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(self._get_option_list(options, ExclusionOptions))
        arg_list.append(repository_or_archive)
        arg_list.extend(paths)

        output = self._run(arg_list, self.archiver.do_list)

        list_result = None

        if common_options.log_json or list_options.json or list_options.json_lines:
            list_result = self._loads_json_lines(output["stdout"])
        else:
            list_result = output["stdout"]

        return self._build_result(("list", list_result))

    def diff(
        self,
        repo_archive_1: str,
        archive_2: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Find the differences (file contents, user/group/mode) between archives.

        :param repo_archive_1: repository location and ARCHIVE1 name
        :type repo_archive_1: str
        :param archive_2: ARCHIVE2 name (no repository location allowed)
        :type archive_2: str
        :param *paths: paths of items inside the archives to compare; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `diff` as well as exclusion, and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        diff_options = self.optionals.get("diff", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("diff")
        arg_list.extend(diff_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionOptions))
        arg_list.append(repo_archive_1)
        arg_list.append(archive_2)
        arg_list.extend(paths)

        output = self._run(arg_list, self.archiver.do_diff)

        diff_result = None
        if common_options.log_json or diff_options.json_lines:
            diff_result = self._loads_json_lines(output["stdout"])
        else:
            diff_result = output["stdout"]

        return self._build_result(("diff", diff_result))

    def delete(
        self,
        repository_or_archive: str,
        *archives: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Delete an archive from the repository or the complete repository

        :param repository_or_archive: repository or archive to delete
        :type repository_or_archive: str
        :param *archives: archives to delete
        :type *archives: Optional[str]
        :param **options: optional arguments specific to `delete` as well as
            archive and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        delete_options = self.optionals.get("delete", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("delete")
        arg_list.extend(delete_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.append(repository_or_archive)
        arg_list.extend(archives)

        output = self._run(arg_list, self.archiver.do_delete)

        stats_result = None
        if delete_options.stats and common_options.log_json:
            stats_result = self._loads_json_lines(output["stats"])
        elif delete_options.stats:
            stats_result = output["stats"]

        return self._build_result(("stats", stats_result))

    def prune(
        self,
        repository: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Prune a repository by deleting all archives not matching any of the specified
        retention options.

        :param repository: repository to prune
        :type repository: str
        :param **options: optional arguments specific to `prune` as well as archive and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        prune_options = self.optionals.get("prune", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("prune")
        arg_list.extend(prune_options.parse())
        arg_list.extend(self._get_option_list(options, ArchivePattern))
        arg_list.append(repository)

        output = self._run(arg_list, self.archiver.do_prune)

        list_result = stats_result = None
        if prune_options.list and not common_options.log_json:
            list_result = output["list"]
        elif prune_options.list and common_options.log_json:
            list_result = self._loads_json_lines(output["list"])
        if prune_options.stats and not common_options.log_json:
            stats_result = output["stats"]
        elif prune_options.stats and common_options.log_json:
            stats_result = self._loads_json_lines(output["stats"])

        return self._build_result(
            ("stats", stats_result),
            ("list", list_result),
        )

    def info(
        self,
        repository_or_archive: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Display detailed information about the specified archive or repository.

        :param repository_or_archive: repository or archive to display information about
        :type repository_or_archive: str
        :param **options: optional arguments specific to `info` as well as archive and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        info_options = self.optionals.get("info", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("info")
        arg_list.extend(info_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.append(repository_or_archive)

        output = self._run(arg_list, self.archiver.do_info)

        info_result = None
        if info_options.json:
            info_result = self._loads_json_lines(output["stdout"])
        else:
            info_result = output["stdout"]

        return self._build_result(("info", info_result))

    def mount(
        self,
        repository_or_archive: str,
        mountpoint: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Mount an archive as a FUSE filesystem.

        :param repository_or_archive: repository or archive to mount
        :type repository_or_archive: str
        :param mountpoint: where to mount filesystem
        :type mountpoint: str
        :param *paths: paths to extract; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `mount` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("mount")
        arg_list.extend(self.optionals.to_list("mount", options))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(repository_or_archive)
        arg_list.append(mountpoint)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_mount)

    def umount(
        self,
        mountpoint: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Un-mount a FUSE filesystem that was mounted with `mount`.

        :param mountpoint: mountpoint of the filesystem to umount
        :type mountpoint: str
        :param **options: optional arguments specific to `umount` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("umount")
        arg_list.append(mountpoint)

        return self._run(arg_list, self.archiver.do_umount)

    def key_change_passphrase(
        self,
        repository: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Change the passphrase protecting the repository encryption.

        :param repository: repository to modify
        :type repository: str
        :param **options: optional arguments specific to `key change-passphrase` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.extend(["key", "change-passphrase"])
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_change_passphrase)

    def key_export(
        self,
        repository: str,
        path: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Copy repository encryption key to another location.

        :param repository: repository to get key for
        :type repository: str
        :param path: where to store the backup
        :type path: str
        :param **options: optional arguments specific to `key export` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.extend(["key", "export"])
        arg_list.extend(self.optionals.to_list("key_export", options))
        arg_list.append(repository)
        arg_list.append(path)

        return self._run(arg_list, self.archiver.do_key_export)

    def key_import(
        self,
        repository: str,
        path: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Restore a key previously backed up with the export command.

        :param repository: repository to get key for
        :type repository: str
        :param path: path to the backup (‘-‘ to read from stdin)
        :type path: str
        :param **options: optional arguments specific to `key import` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.extend(["key", "import"])
        arg_list.extend(self.optionals.to_list("key_import", options))
        arg_list.append(repository)
        arg_list.append(path)

        return self._run(arg_list, self.archiver.do_key_import)

    def upgrade(
        self,
        repository: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Upgrade an existing, local Borg repository.

        :param repository: path to the repository to be upgraded
        :type repository: str
        :param **options: optional arguments specific to `upgrade` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("upgrade")
        arg_list.extend(self.optionals.to_list("upgrade", options))
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_upgrade)

    def export_tar(
        self,
        archive: str,
        file: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Create a tarball from an archive.

        :param archive: archive to export
        :type archive: str
        :param file: output tar file. “-” to write to stdout instead.
        :type file: str
        :param *paths: paths of items inside the archives to compare; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `export-tar` as well as exclusion and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        export_tar_options = self.optionals.get("export_tar", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("export-tar")
        arg_list.extend(export_tar_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(archive)
        arg_list.append(file)
        arg_list.extend(paths)

        output = self._run(arg_list, self.archiver.do_export_tar, raw_bytes=(file == "-"))

        list_result = export_result = None
        if export_tar_options.list:
            list_result = output["list"]
        if file == "-":
            export_result = output["stdout"]

        return self._build_result(
            ("list", list_result),
            ("tar", export_result),
        )

    def serve(
        self,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Start a repository server process. This command is usually not used manually.

        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("serve")
        arg_list.extend(self.optionals.to_list("serve", options))

        return self._run(arg_list, self.archiver.do_serve)

    def config(
        self,
        repository: str,
        *changes: Union[str, Tuple[str, str]],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Get and set options in a local repository or cache config file.

        :param repository: repository to configure
        :type repository: str
        :param *changes: config key, new value
        :type *changes: Union[str, Tuple[str, str]]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)
        config_options = self.optionals.get("config", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("config")
        arg_list.extend(config_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(repository)

        change_result = []
        list_result = None
        if not changes:
            output = self._run(arg_list, self.archiver.do_config)
            if config_options.list:
                list_result = output["stdout"]

        for change in changes:
            if isinstance(change, tuple):
                change = arg_list + [change[0], change[1]]
                self._run(change, self.archiver.do_config)
            else:
                change = arg_list + [change]
                output = self._run(change, self.archiver.do_config)
                change_result.append(output["stdout"])

        return self._build_result(
            ("changes", change_result),
            ("list", list_result),
        )

    def with_lock(
        self,
        repository: str,
        command: str,
        *args: Union[str, int],
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Run a user-specified command while the repository lock is held.

        :param repository: repository to lock
        :type repository: str
        :param command: command to run
        :type command: str
        :param *args: command arguments
        :type *args: Union[str, int]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("with-lock")
        arg_list.append(repository)
        arg_list.append(command)
        arg_list.extend(args)

        return self._run(arg_list, self.archiver.do_with_lock)

    def break_lock(
        self, repository: str, **options: Union[bool, str, int]
    ) -> BorgRunOutput:
        """Break the repository and cache locks.

        :param repository: repository for which to break the locks
        :type repository: str
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("break-lock")
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_break_lock)

    def benchmark_crud(
        self,
        repository: str,
        path: str,
        **options: Union[bool, str, int],
    ) -> BorgRunOutput:
        """Benchmark borg CRUD (create, read, update, delete) operations.

        :param repository: repository to use for benchmark (must exist)
        :type repository: str
        :param path: path were to create benchmark input data
        :type path: str
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: BorgRunOutput
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.extend(["benchmark", "crud"])
        arg_list.append(repository)
        arg_list.append(path)

        output = self._run(arg_list, self.archiver.do_benchmark_crud)

        benchmark_result = output["stdout"]

        return self._build_result(("benchmark", benchmark_result))
