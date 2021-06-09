"""Run Borg Backups"""

import logging
import os
import sys
from dataclasses import dataclass
from io import StringIO
from json import decoder, loads
from typing import Callable, List, Optional, Union

import borg.archive
import borg.archiver
import borg.helpers
import borg.repository
from dotenv import dotenv_values, load_dotenv

from .options import (
    ArchiveInput,
    ArchiveOutput,
    ArchivePattern,
    CommonOptions,
    ExclusionInput,
    ExclusionOptions,
    ExclusionOutput,
    FilesystemOptions,
    OptionsBase,
)

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
        self.defaults = defaults or {}
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

    def _run(self, arg_list: List, func: Callable) -> Union[str, dict, None]:
        stdout_run = stderr_run = None
        self._logger.debug("%s: %s", func.__name__, arg_list)
        arg_list.insert(0, "borgapi")
        args = self.archiver.get_args(arg_list, os.environ.get("SSH_ORIGINAL_COMMAND"))

        original_stderr = sys.stderr

        sys.stdout = stdout_temp = StringIO()
        sys.stderr = stderr_temp = StringIO()
        try:
            func(args)
        except Exception as e:
            self._logger.error(e)
            raise e
        else:
            stdout_run = stdout_temp.getvalue().strip()
            stderr_run = stderr_temp.getvalue().strip()
        finally:
            sys.stdout.close()
            sys.stdout = self.original_stdout
            sys.stderr = original_stderr
            stdout_temp.close()
            stderr_temp.close()

        if getattr(args, "json", False) or getattr(args, "json_lines", False):
            stdout_json = stderr_json = None
            if stdout_run:
                try:
                    stdout_json = loads(stdout_run)
                except decoder.JSONDecodeError:
                    clean_json = f'[{",".join(stdout_run.splitlines())}]'
                    try:
                        stdout_json = loads(clean_json)
                    except decoder.JSONDecodeError:
                        stdout_json = (stdout_run or None)
            if stderr_run:
                try:
                    stderr_json = loads(stderr_run)
                except decoder.JSONDecodeError:
                    clean_json = f'[{",".join(stderr_run.splitlines())}]'
                    try:
                        stderr_json = loads(clean_json)
                    except decoder.JSONDecodeError:
                        stderr_json = (stderr_run or None)
            return stdout_json, stderr_json
        return (stdout_run or None), (stderr_run or None)

    def _get_option_list(self, value: dict, options_class: OptionsBase) -> List:
        args = self.options | (value or {})
        return options_class(**args).parse()

    def _get_command_list(
        self,
        command: str,
        values: dict,
        options_class: OptionsBase,
    ) -> List:
        optionals = self.defaults.get(command, {}) | (values or {})
        return options_class(**optionals).parse()

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
        load_dotenv(stream=config)

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
        variables = (
            [k for k in variable if k in os.environ] or
            [k for k in self._previous_dotenv if k in os.environ]
        )
        for var in variables:
            del os.environ[var]

    def init(
        self,
        repository: str,
        encryption: str = "repokey",
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            append_only: bool = False
            storage_quota: str = None
            make_parent_dirs: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("init")
        arg_list.extend(["--encryption", encryption])
        arg_list.extend(self._get_command_list("init", options, _Optional))
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_init)

    def create(
        self,
        archive: str,
        *paths: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            dry_run: bool = False
            stats: bool = False
            list: bool = False
            filter: str = None
            json: bool = False
            no_cache_sync: bool = False
            no_files_cache: bool = False
            stdin_name: str = None
            stdin_user: str = None
            stdin_group: str = None
            stdin_mode: str = None

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("create")
        arg_list.extend(self._get_command_list("create", options, _Optional))
        arg_list.extend(self._get_option_list(options, ExclusionInput))
        arg_list.extend(self._get_option_list(options, FilesystemOptions))
        arg_list.extend(self._get_option_list(options, ArchiveInput))
        arg_list.append(archive)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_create)

    def extract(
        self,
        archive: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            list: bool = False
            dry_run: bool = False
            numeric_owner: bool = False
            nobsdflags: bool = False
            noacls: bool = False
            noxattrs: bool = False
            stdout: bool = False
            sparse: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("extract")
        arg_list.extend(self._get_command_list("extract", options, _Optional))
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(archive)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_extract)

    def check(
        self,
        *repository_or_archive: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Verify the consistency of a repository and the corresponding archives.

        :param *repository_or_archive: repository or archive to check consistency of
        :type *repository_or_archive: str
        :param **options: optional arguments specific to `check` as well as archive
            and common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            repository_only: bool = False
            archives_only: bool = False
            verify_data: bool = False
            repair: bool = False
            save_space: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("check")
        arg_list.extend(self._get_command_list("check", options, _Optional))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(repository_or_archive)

        return self._run(arg_list, self.archiver.do_check)

    def rename(
        self,
        archive: str,
        newname: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
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
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            short: bool = False
            format: str = None
            json: bool = False
            json_lines: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("list")
        arg_list.extend(self._get_command_list("list", options, _Optional))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(self._get_option_list(options, ExclusionOptions))
        arg_list.append(repository_or_archive)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_list)

    def diff(
        self,
        repo_archive_1: str,
        archive_2: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            numeric_owner: bool = False
            same_chunker_params: bool = False
            sort: bool = False
            json_lines: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("diff")
        arg_list.extend(self._get_command_list("diff", options, _Optional))
        arg_list.extend(self._get_option_list(options, ExclusionOptions))
        arg_list.append(repo_archive_1)
        arg_list.append(archive_2)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_diff)

    def delete(
        self,
        repository_or_archive: str,
        *archives: Optional[str],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            dry_run: bool = False
            stats: bool = False
            cache_only: bool = False
            force: bool = False
            save_space: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("delete")
        arg_list.extend(self._get_command_list("delete", options, _Optional))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.append(repository_or_archive)
        arg_list.extend(archives)

        return self._run(arg_list, self.archiver.do_delete)

    def prune(
        self,
        repository: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Prune a repository by deleting all archives not matching any of the specified
        retention options.

        :param repository: repository to prune
        :type repository: str
        :param **options: optional arguments specific to `prune` as well as archive and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        # pylint: disable=too-many-instance-attributes
        @dataclass
        class _Optional(OptionsBase):
            dry_run: bool = False
            force: bool = False
            stats: bool = False
            list: bool = False
            keep_within: str = None
            keep_last: int = None
            keep_secondly: int = None
            keep_minutely: int = None
            keep_hourly: int = None
            keep_daily: int = None
            keep_weekly: int = None
            keep_monthly: int = None
            keep_yearly: int = None
            save_space: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("prune")
        arg_list.extend(self._get_command_list("prune", options, _Optional))
        arg_list.extend(self._get_option_list(options, ArchivePattern))
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_prune)

    def info(
        self,
        repository_or_archive: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Display detailed information about the specified archive or repository.

        :param repository_or_archive: repository or archive to display information about
        :type repository_or_archive: str
        :param **options: optional arguments specific to `info` as well as archive and
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            json: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("info")
        arg_list.extend(self._get_command_list("info", options, _Optional))
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.append(repository_or_archive)

        return self._run(arg_list, self.archiver.do_info)

    def mount(
        self,
        repository_or_archive: str,
        mountpoint: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        # pylint: disable=invalid-name
        @dataclass
        class _Optional(OptionsBase):
            foreground: bool = False
            o: str = None

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("mount")
        arg_list.extend(self._get_command_list("mount", options, _Optional))
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
    ) -> Union[str, dict, None]:
        """Un-mount a FUSE filesystem that was mounted with `mount`.

        :param mountpoint: mountpoint of the filesystem to umount
        :type mountpoint: str
        :param **options: optional arguments specific to `umount` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
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
    ) -> Union[str, dict, None]:
        """Change the passphrase protecting the repository encryption.

        :param repository: repository to modify
        :type repository: str
        :param **options: optional arguments specific to `key change-passphrase` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
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
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            paper: bool = False
            qr_html: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.extend(["key", "export"])
        arg_list.extend(self._get_command_list("key_export", options, _Optional))
        arg_list.append(repository)
        arg_list.extend(path)

        return self._run(arg_list, self.archiver.do_key_export)

    def key_import(
        self,
        repository: str,
        path: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            paper: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.extend(["key", "import"])
        arg_list.extend(self._get_command_list("key_import", options, _Optional))
        arg_list.append(repository)
        arg_list.extend(path)

        return self._run(arg_list, self.archiver.do_key_import)

    def upgrade(
        self,
        repository: str,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Upgrade an existing, local Borg repository.

        :param repository: path to the repository to be upgraded
        :type repository: str
        :param **options: optional arguments specific to `upgrade` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            dry_run: bool = False
            inplace: bool = False
            force: bool = False
            tam: bool = False
            disable_tam: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("upgrade")
        arg_list.extend(self._get_command_list("upgrade", options, _Optional))
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_upgrade)

    def export_tar(
        self,
        archive: str,
        file: str,
        *paths: Optional[str],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            tar_filter: str = None
            list: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("export-tar")
        arg_list.extend(self._get_command_list("export_tar", options, _Optional))
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(archive)
        arg_list.append(file)
        arg_list.extend(paths)

        return self._run(arg_list, self.archiver.do_export_tar)

    def serve(
        self,
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Start a repository server process. This command is usually not used manually.

        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            restrict_to_path: str = None
            restrict_to_repository: str = None
            append_only: bool = False
            storage_quota: str = None

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("serve")
        arg_list.extend(self._get_command_list("serve", options, _Optional))

        return self._run(arg_list, self.archiver.do_serve)

    def config(
        self,
        repository: str,
        changes: List[tuple[str, str]],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
        """Get and set options in a local repository or cache config file.

        :param repository: repository to configure
        :type repository: str
        :param changes: list of config key, new value tuples
        :type changes: list[(str,str)]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(OptionsBase):
            cache: bool = False
            delete: bool = False
            list: bool = False

            # pylint: disable=useless-super-delegation
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("config")
        arg_list.extend(self._get_command_list("config", options, _Optional))
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(repository)
        if changes:
            for name, value in changes:
                change = arg_list + [name, value]
                return self._run(change, self.archiver.do_config)
        else:
            return self._run(arg_list, self.archiver.do_config)

    def with_lock(
        self,
        repository: str,
        command: str,
        *args: Union[str, int],
        **options: Union[bool, str, int],
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
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
    ) -> Union[str, dict, None]:
        """Break the repository and cache locks.

        :param repository: repository for which to break the locks
        :type repository: str
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Union[bool, str, int]
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("break-lock")
        arg_list.append(repository)

        return self._run(arg_list, self.archiver.do_break_lock)

    def benchmark_crud(
        self, repository: str, path: str, **options: Union[bool, str, int]
    ) -> Union[str, dict, None]:
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
        :rtype: Union[str, dict, None]
        """

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("benchmark crud")
        arg_list.append(repository)
        arg_list.append(path)

        return self._run(arg_list, self.archiver.do_benchmark_crud)
