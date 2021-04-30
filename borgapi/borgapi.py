"""Run Borg Backups"""

import logging
import os
import sys
from dataclasses import dataclass
from io import StringIO
from json import loads
from typing import Callable, List, Optional, Union

import borg.archive
import borg.archiver
import borg.helpers
import borg.repository

from .options import (
    ArchiveInput,
    ArchiveOutput,
    ArchivePattern,
    CommonOptions,
    ExclusionInput,
    ExclusionOptions,
    ExclusionOutput,
    FilesystemOptions,
    Options,
)


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
        self.logger_setup = False
        self.archiver = borg.archiver.Archiver()
        self.archiver.log_json = log_json
        borg.archiver.setup_logging(level=log_level, is_serve=False, json=log_json)
        self.original_stdout = sys.stdout

    def _run(self, arg_list: List, func: Callable) -> Union[str, dict, None]:
        capture = value = None
        logging.debug("%s: %s", func.__name__, arg_list)
        args = self.archiver.get_args(arg_list, os.environ.get("SSH_ORIGINAL_COMMAND"))

        sys.stdout = temp_stdout = StringIO()
        try:
            func(args)
        except Exception as e:
            logging.error(e)
            raise e
        else:
            value = temp_stdout.getvalue()
        finally:
            sys.stdout = self.original_stdout
            temp_stdout.close()

        if getattr(args, "json", False) and value:
            capture = loads(value)
        elif value:
            capture = value

        return capture

    def _get_option_list(self, value: dict, options_class: Options) -> List:
        args = self.options | (value or {})
        return options_class(**args).parse()

    def _get_command_list(
        self,
        command: str,
        values: dict,
        options_class: Options,
    ) -> List:
        optionals = self.defaults.get(command, {}) | (values or {})
        return options_class(**optionals).parse()

    def init(
        self,
        repository: str,
        encryption: str = "repokey",
        **options: dict,
    ) -> Union[str, dict, None]:
        """Initialize an empty repository. A repository is a filesystem directory
        containing the deduplicated data from zero or more archives.

        :param repository: repository to create
        :type repository: str
        :param encryption: select encryption key mode; defaults to "repokey"
        :type encryption: str, optional
        :param **options: optional arguments specific to `init` and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            json dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *paths: tuple[str],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Create a backup archive containing all files found while recursively
        traversing all paths specified.

        :param archive: name of archive to create (must be also a valid directory name)
        :type archive: str
        :param paths: paths to archive
        :type paths: tuple[str]
        :param **options: optional arguments specific to `create` as well as exclusion,
            filesysem, archive, and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *paths: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Extract the contents of an archive.

        :param archive: archive to extract
        :type archive: str
        :param paths: paths to archive
        :type paths: Optional[tuple[str]]
        :param **options: optional arguments specific to `extract` as well as exclusion
            and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *repository_or_archive: tuple[str],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Verify the consistency of a repository and the corresponding archives.

        :param repository_or_archive: repository or archive to check consistency of
        :type repository_or_archive: tuple[str]
        :param **options: optional arguments specific to `check` as well as archive
            and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Rename an archive in the repository.

        :param archive: archive to rename
        :type archive: str
        :param newname: the new archive name to use
        :type newname: str
        :param **options: optional arguments specific to `rename` as well as
            common options; defaults to {}
        :type **options: keyword args
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
        *paths: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """List the contents of a repository or an archive.

        :param repository_or_archive: repository or archive to list contents of
        :type repository_or_archive: str
        :param paths: paths to list; patterns are supported
        :type paths: Optional[tuple[str]]
        :param **options: optional arguments specific to `list` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *paths: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Find the differences (file contents, user/group/mode) between archives.

        :param repo_archive_1: repository location and ARCHIVE1 name
        :type repo_archive_1: str
        :param archive_2: ARCHIVE2 name (no repository location allowed)
        :type archive_2: str
        :param paths: paths of items inside the archives to compare; patterns are supported
        :type paths: Optional[tuple[str]]
        :param **options: optional arguments specific to `diff` as well as exclusion, and
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *archives: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Delete an archive from the repository or the complete repository

        :param repository_or_archive: repository or archive to delete
        :type repository_or_archive: str
        :param archives: archives to delete
        :type archives: Optional[tuple[str]]
        :param **options: optional arguments specific to `delete` as well as
            archive and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Prune a repository by deleting all archives not matching any of the specified
        retention options.

        :param repository: repository to prune
        :type repository: str
        :param **options: optional arguments specific to `prune` as well as archive and
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        # pylint: disable=too-many-instance-attributes
        @dataclass
        class _Optional(Options):
            dry_run: bool = False
            force: bool = False
            stats: bool = False
            list: bool = False
            keep_within: str = None
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Display detailed information about the specified archive or repository.

        :param repository_or_archive: repository or archive to display information about
        :type repository_or_archive: str
        :param **options: optional arguments specific to `info` as well as archive and
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *paths: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Mount an archive as a FUSE filesystem.

        :param repository_or_archive: repository or archive to mount
        :type repository_or_archive: str
        :param mountpoint: where to mount filesystem
        :type mountpoint: str
        :param paths: paths to extract; patterns are supported
        :type paths: Optional[tuple[str]]
        :param **options: optional arguments specific to `mount` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
            foreground: bool = False

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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Un-mount a FUSE filesystem that was mounted with `mount`.

        :param mountpoint: mountpoint of the filesystem to umount
        :type mountpoint: str
        :param **options: optional arguments specific to `umount` as well as
            common options; defaults to {}
        :type **options: keyword args
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Change the passphrase protecting the repository encryption.

        :param repository: repository to modify
        :type repository: str
        :param **options: optional arguments specific to `key change-passphrase` as well as
            common options; defaults to {}
        :type **options: keyword args
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Copy repository encryption key to another location.

        :param repository: repository to get key for
        :type repository: str
        :param path: where to store the backup
        :type path: str
        :param **options: optional arguments specific to `key export` as well as
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Restore a key previously backed up with the export command.

        :param repository: repository to get key for
        :type repository: str
        :param path: path to the backup (‘-‘ to read from stdin)
        :type path: str
        :param **options: optional arguments specific to `key import` as well as
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        **options: dict,
    ) -> Union[str, dict, None]:
        """Upgrade an existing, local Borg repository.

        :param repository: path to the repository to be upgraded
        :type repository: str
        :param **options: optional arguments specific to `upgrade` as well as
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
        *paths: Optional[tuple[str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Create a tarball from an archive.

        :param archive: archive to export
        :type archive: str
        :param file: output tar file. “-” to write to stdout instead.
        :type file: str
        :param paths: paths of items inside the archives to compare; patterns are supported
        :type paths: Optional[tuple[str]]
        :param **options: optional arguments specific to `export-tar` as well as exclusion and
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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

    def config(
        self,
        repository: str,
        changes: List[tuple[str, str]],
        **options: dict,
    ) -> Union[str, dict, None]:
        """Get and set options in a local repository or cache config file.

        :param repository: repository to configure
        :type repository: str
        :param changes: list of config key, new value tuples
        :type changes: list[(str,str)]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: keyword args
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Union[str, dict, None]
        """

        @dataclass
        class _Optional(Options):
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
