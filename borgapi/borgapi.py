"""Run Borg backups."""

import functools
import logging
import os
from asyncio import wrap_future
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from json import decoder, loads
from typing import Callable, Optional, Union

import borg.archiver
from dotenv import dotenv_values, load_dotenv

from .capture import LOG_LVL, OutputCapture, OutputOptions
from .helpers import ENVIRONMENT_DEFAULTS, Options, Output
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

__all__ = ["BorgAPI", "BorgAPIAsync"]


class BorgAPIBase:
    """Automate borg in code.

    Base class for the wrapper. Contains all the non-Borg command calls.
    Should not be called by itself. Only really here for readability purposes.
    """

    def __init__(
        self,
        defaults: dict = None,
        options: dict = None,
        log_level: str = LOG_LVL,
        log_json: bool = False,
        environ: dict = None,
    ):
        """Set the options to be used across the different command call.

        :param defaults: options for specific commands to always use, defaults to None
        :type defaults: dict, optional
        :param options: common flags for all commands, defaults to None
        :type options: dict, optional
        :param log_level: level to record logged messages at, defaults to LOG_LVL
        :type log_level: str, optional
        :param log_json: if the output should be in json or string format, defaults to False
        :type log_json: bool, optional
        :param environ: envirnmental variables to set for borg to use (ie BORG_PASSCOMMAND),
            defaults to None
        :type environ: dict, optional
        """
        self.options = options or {}
        self.optionals = CommandOptions(defaults)
        self.archiver = borg.archiver.Archiver()
        self._previous_dotenv = []
        self._set_environ_defaults()
        if environ is not None:
            self.set_environ(**environ)
        self.log_level = log_level
        if log_json:
            self.options.set("log_json", log_json)

        self.archiver.log_json = log_json
        borg.archiver.setup_logging(level=self.log_level, is_serve=False, json=log_json)
        logging.getLogger("borgapi")
        self._logger = logging.getLogger(__name__)

        self.output = OutputCapture()

    @staticmethod
    def _loads_json_lines(string: Union[str, list]) -> Union[dict, str, None]:
        result = None
        try:
            if type(string) is str:
                result = loads(string)
            elif type(string) is list:
                result = loads(f"[{','.join(string)}]")
        except decoder.JSONDecodeError:
            if type(string) is str:
                clean = f"[{','.join(string.splitlines())}]"
            elif type(string) is str:
                clean = str(string)
            try:
                result = loads(clean)
            except decoder.JSONDecodeError:
                try:
                    multiline = "[" + string.replace("}{", "},{") + "]"
                    result = loads(multiline)
                except decoder.JSONDecodeError:
                    result = string or None
        return result

    @staticmethod
    def _build_result(*results: tuple[str, Output], log_json: bool = False) -> Output:
        if not results:
            return None
        if len(results) == 1:
            result = results[0][1]
            if len(result) == 1:
                return result[0]
            return result
        result = {}
        for name, value in results:
            result[name] = value
        return result

    def _run(
        self,
        arg_list: list,
        func: Callable,
        output_options: OutputOptions,
    ) -> dict:
        self._logger.debug("%s: %s", func.__name__, arg_list)
        arg_list.insert(0, "borgapi")
        arg_list = [str(arg) for arg in arg_list]
        args = self.archiver.get_args(arg_list, os.getenv("SSH_ORIGINAL_COMMAND", None))

        prev_json = self.archiver.log_json
        log_json = getattr(args, "log_json", prev_json)
        self.archiver.log_json = log_json

        with self.output(output_options):
            try:
                func(args)
            except Exception as e:
                self._logger.error(e)
                raise e
            else:
                capture_result = self.output.getvalues()

        self.archiver.log_json = prev_json

        return capture_result

    def _get_option(self, value: dict, options_class: OptionsBase) -> OptionsBase:
        args = {**self.options, **(value or {})}
        return options_class(**args)

    def _get_option_list(self, value: dict, options_class: OptionsBase) -> list:
        option = self._get_option(value, options_class)
        return option.parse()

    def _get_log_level(self, options: dict) -> str:
        lvl = self.log_level
        if options.get("critical", False):
            lvl = "critical"
        elif options.get("error", False):
            lvl = "error"
        elif options.get("warning", False):
            lvl = "warning"
        elif options.get("info", False) or options.get("verbose", False):
            lvl = "info"
        elif options.get("debug", False):
            lvl = "debug"

        elif self.options.get("critical", False):
            lvl = "critical"
        elif self.options.get("error", False):
            lvl = "error"
        elif self.options.get("warning", False):
            lvl = "warning"
        elif self.options.get("info", False) or self.options.get("verbose", False):
            lvl = "info"
        elif self.options.get("debug", False):
            lvl = "debug"

        return lvl

    def _get_basic_results(self, output: dict, opts: OutputOptions) -> dict:
        result_list = []
        if opts.stats_show:
            if opts.stats_json:
                result_list.append(("stats", self._loads_json_lines(output["stdout"])))
            else:
                result_list.append(("stats", output["stats"]))

        if opts.list_show:
            if opts.list_json:
                result_list.append(("list", self._loads_json_lines(output["list"])))
            else:
                result_list.append(("list", output["list"]))

        if opts.prog_show:
            if opts.prog_json:
                result_list.append(("prog", self._loads_json_lines(output["stderr"])))
            else:
                result_list.append(("prog", output["stderr"]))

        return result_list

    def _set_environ_defaults(self):
        for key, value in ENVIRONMENT_DEFAULTS.items():
            if os.getenv(key) is None:
                os.environ[key] = value


class BorgAPI(BorgAPIBase):
    """Automate borg in code."""

    def __init__(
        self,
        defaults: dict = None,
        options: dict = None,
        log_level: str = LOG_LVL,
        log_json: bool = False,
        environ: dict = None,
    ):
        """Set the options to be used across the different command call.

        :param defaults: options for specific commands to always use, defaults to None
        :type defaults: dict, optional
        :param options: common flags for all commands, defaults to None
        :type options: dict, optional
        :param log_level: level to record logged messages at, defaults to LOG_LVL
        :type log_level: str, optional
        :param log_json: if the output should be in json or string format, defaults to False
        :type log_json: bool, optional
        """
        super().__init__(defaults, options, log_level, log_json, environ)

    def set_environ(
        self,
        filename: str = None,
        dictionary: dict = None,
        **kwargs: Options,
    ) -> None:
        """Load environment variables from file.

        If nothing is provided, load_dotenv's default value will be used.

        :param filename: path to environment file, defaults to None
        :type filename: str, optional
        :param dictionary: dictionary of environment variables to load, defaults to None
        :type dictionary: dict, optional
        :param **kwargs: Environment variables and their values as named args
        :type **kwargs: Options
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

        with StringIO() as config:
            for key, value in variables.items():
                config.write(f"{key}={value}\n")
            config.seek(0)
            load_dotenv(stream=config, override=True)
            config.close()

    def unset_environ(self, *variable: Optional[str]) -> None:
        """Remove variables from the environment.

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
        **options: Options,
    ) -> Output:
        """Initialize an empty repository.

        A repository is a filesystem directory containing the deduplicated data
        from zero or more archives.

        :param repository: repository to create
        :type repository: str
        :param encryption: select encryption key mode; defaults to "repokey"
        :type encryption: str, optional
        :param **options: optional arguments specific to `init` and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            json dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        init_options = self.optionals.get("init", options)

        arg_list = []
        arg_list.extend(self._get_option_list(options, CommonOptions))
        arg_list.append("init")
        arg_list.extend(["--encryption", encryption])
        arg_list.extend(init_options.parse())
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_init, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def create(
        self,
        archive: str,
        *paths: str,
        **options: Options,
    ) -> Output:
        """Create a backup archive of all files found while recursively traversing specified paths.

        :param archive: name of archive to create (must be also a valid directory name)
        :type archive: str
        :param *paths: paths to archive
        :type *paths: str
        :param **options: optional arguments specific to `create` as well as exclusion,
            filesysem, archive, and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            stats_show=create_options.stats or create_options.json,
            stats_json=create_options.json,
            list_show=create_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_create, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        if opts.list_show:
            if opts.list_json:
                result_list.remove(("list", []))
                result_list.append(("list", self._loads_json_lines(output["stderr"])))
        return self._build_result(*result_list, log_json=opts.log_json)

    def extract(
        self,
        archive: str,
        *paths: Optional[str],
        **options: Options,
    ) -> Output:
        """Extract the contents of an archive.

        :param archive: archive to extract
        :type archive: str
        :param *paths: paths to archive
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `extract` as well as exclusion
            and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            raw_bytes=extract_options.stdout,
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            list_show=extract_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(
            arg_list,
            self.archiver.do_extract,
            output_options=opts,
        )

        result_list = self._get_basic_results(output, opts)
        if opts.raw_bytes:
            result_list.append(("extract", output["stdout"]))

        return self._build_result(*result_list, log_json=opts.log_json)

    def check(self, *repository_or_archive: str, **options: Options) -> Output:
        """Verify the consistency of a repository and the corresponding archives.

        :param *repository_or_archive: repository or archive to check consistency of
        :type *repository_or_archive: str
        :param **options: optional arguments specific to `check` as well as archive
            and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        check_options = self.optionals.get("check", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("check")
        arg_list.extend(check_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(repository_or_archive)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_check, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def rename(
        self,
        archive: str,
        newname: str,
        **options: Options,
    ) -> Output:
        """Rename an archive in the repository.

        :param archive: archive to rename
        :type archive: str
        :param newname: the new archive name to use
        :type newname: str
        :param **options: optional arguments specific to `rename` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("rename")
        arg_list.append(archive)
        arg_list.append(newname)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_rename, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def list(
        self,
        repository_or_archive: str,
        *paths: Optional[str],
        **options: Options,
    ) -> Output:
        """List the contents of a repository or an archive.

        :param repository_or_archive: repository or archive to list contents of
        :type repository_or_archive: str
        :param *paths: paths to list; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `list` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            list_show=True,
            list_json=list_options.json_lines or list_options.json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_list, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        if opts.list_show:
            if opts.list_json:
                result_list.remove(("list", []))
                result_list.append(("list", self._loads_json_lines(output["stdout"])))
            else:
                result_list.remove(("list", ""))
                result_list.append(("list", output["stdout"]))

        return self._build_result(*result_list, log_json=opts.log_json)

    def diff(
        self,
        repo_archive_1: str,
        archive_2: str,
        *paths: Optional[str],
        **options: Options,
    ) -> Output:
        """Find the differences (file contents, user/group/mode) between archives.

        :param repo_archive_1: repository location and ARCHIVE1 name
        :type repo_archive_1: str
        :param archive_2: ARCHIVE2 name (no repository location allowed)
        :type archive_2: str
        :param *paths: paths of items inside the archives to compare; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `diff` as well as exclusion, and
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=diff_options.json_lines or common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_diff, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        if opts.log_json:
            result_list.append(("diff", self._loads_json_lines(output["stdout"])))
        else:
            result_list.append(("diff", output["stdout"]))

        return self._build_result(*result_list, log_json=opts.log_json)

    def delete(
        self,
        repository_or_archive: str,
        *archives: Optional[str],
        **options: Options,
    ) -> Output:
        """Delete an archive from the repository or the complete repository.

        :param repository_or_archive: repository or archive to delete
        :type repository_or_archive: str
        :param *archives: archives to delete
        :type *archives: Optional[str]
        :param **options: optional arguments specific to `delete` as well as
            archive and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            # no json option in this command
            stats_show=delete_options.stats,  # or delete_options.json,
            # stats_json = delete_options.json,
            list_show=delete_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_delete, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def prune(self, repository: str, **options: Options) -> Output:
        """Prune a repository by deleting all archives not matching the specified retention options.

        :param repository: repository to prune
        :type repository: str
        :param **options: optional arguments specific to `prune` as well as archive and
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        prune_options = self.optionals.get("prune", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("prune")
        arg_list.extend(prune_options.parse())
        arg_list.extend(self._get_option_list(options, ArchivePattern))
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            # no json option for stats
            stats_show=prune_options.stats,  # or prune_options.json,
            # stats_json = prune_options.json,
            list_show=prune_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_prune, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def compact(self, repository: str, **options: Options) -> Output:
        """Compact frees repository space by compacting segments.

        :param repository: repository to compact
        :type repository: str
        :param **options: optional arguments specific to `compact` as well as archive and
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        compact_options = self.optionals.get("compact", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("compact")
        arg_list.extend(compact_options.parse())
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            repo_show=common_options.verbose,
            repo_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_compact, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        if opts.repo_show:
            if opts.repo_json:
                result_list.append(("compact", self._loads_json_lines(output["repo"])))
            else:
                result_list.append(("compact", output["repo"]))
        return self._build_result(*result_list, log_json=opts.log_json)

    def info(self, repository_or_archive: str, **options: Options) -> Output:
        """Display detailed information about the specified archive or repository.

        :param repository_or_archive: repository or archive to display information about
        :type repository_or_archive: str
        :param **options: optional arguments specific to `info` as well as archive and
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        info_options = self.optionals.get("info", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("info")
        arg_list.extend(info_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.append(repository_or_archive)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=info_options.json or common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_info, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        if opts.log_json:
            result_list.append(("info", self._loads_json_lines(output["stdout"])))
        else:
            result_list.append(("info", output["stdout"]))

        return self._build_result(*result_list, log_json=opts.log_json)

    def mount(
        self,
        repository_or_archive: str,
        mountpoint: str,
        *paths: Optional[str],
        **options: Options,
    ) -> Output:
        """Mount an archive as a FUSE filesystem.

        :param repository_or_archive: repository or archive to mount
        :type repository_or_archive: str
        :param mountpoint: where to mount filesystem
        :type mountpoint: str
        :param *paths: paths to extract; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `mount` as well as exclusion,
            archive, and common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        mount_options = self.optionals.get("mount", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("mount")
        arg_list.extend(mount_options.parse())
        arg_list.extend(self._get_option_list(options, ArchiveOutput))
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(repository_or_archive)
        arg_list.append(mountpoint)
        arg_list.extend(paths)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )

        pid = os.fork()
        # child process, this one does the actual mount (in the foreground)
        if pid == 0:
            output = self._run(arg_list, self.archiver.do_mount, output_options=opts)

            result_list = self._get_basic_results(output, opts)
            return self._build_result(*result_list, log_json=opts.log_json)

        result_list = self._get_basic_results({}, opts)
        result_list.append(("mount", {"pid": pid, "cid": os.getpid()}))
        return self._build_result(*result_list, log_json=opts.log_json)

    def umount(self, mountpoint: str, **options: Options) -> Output:
        """Un-mount a FUSE filesystem that was mounted with `mount`.

        :param mountpoint: mountpoint of the filesystem to umount
        :type mountpoint: str
        :param **options: optional arguments specific to `umount` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("umount")
        arg_list.append(mountpoint)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_umount, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def key_change_passphrase(self, repository: str, **options: Options) -> Output:
        """Change the passphrase protecting the repository encryption.

        :param repository: repository to modify
        :type repository: str
        :param **options: optional arguments specific to `key change-passphrase` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.extend(["key", "change-passphrase"])
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_change_passphrase, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def key_export(
        self,
        repository: str,
        path: str,
        **options: Options,
    ) -> Output:
        """Copy repository encryption key to another location.

        :param repository: repository to get key for
        :type repository: str
        :param path: where to store the backup
        :type path: str
        :param **options: optional arguments specific to `key export` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        key_export_options = self.optionals.get("key_export", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.extend(["key", "export"])
        arg_list.extend(key_export_options.parse())
        arg_list.append(repository)
        arg_list.append(path)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_key_export, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def key_import(
        self,
        repository: str,
        path: str,
        **options: Options,
    ) -> Output:
        """Restore a key previously backed up with the export command.

        :param repository: repository to get key for
        :type repository: str
        :param path: path to the backup (‘-‘ to read from stdin)
        :type path: str
        :param **options: optional arguments specific to `key import` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        key_import_options = self.optionals.get("key_import", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.extend(["key", "import"])
        arg_list.extend(key_import_options.parse())
        arg_list.append(repository)
        arg_list.append(path)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_key_import, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def upgrade(self, repository: str, **options: Options) -> Output:
        """Upgrade an existing, local Borg repository.

        :param repository: path to the repository to be upgraded
        :type repository: str
        :param **options: optional arguments specific to `upgrade` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        upgrade_options = self.optionals.to_list("upgrade", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("upgrade")
        arg_list.extend(upgrade_options.parse())
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_upgrade, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def recreate(
        self,
        repository_or_archive: str,
        *paths: Optional[str],
        **options: Options,
    ):
        """Recreate the contents of existing archives.

        :param repository_or_archive: repository or archive to recreate
        :type repository_or_archive: str
        :param *paths: paths to recreate; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `recreate` as well as exclusion and
            common options; defaults to {}
        :type **options: Options
        :return: Output of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        recreate_options = self.optionals.get("recreate", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("recreate")
        arg_list.extend(recreate_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionInput))
        arg_list.extend(self._get_option_list(options, ArchiveInput))
        arg_list.append(repository_or_archive)
        arg_list.extend(paths)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            stats_show=recreate_options.stats,
            stats_json=False,  # No json flag
            list_show=recreate_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_recreate, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def import_tar(
        self,
        archive: str,
        tarfile: str,
        **options: Options,
    ):
        """Create a backup archive from a tarball.

        :param archive: name of archive to create (must be also a valid directory name)
        :type archive: str
        :param tarfile: input tar file. “-” to read from stdin instead.
        :type tarfile: str
        :param **options: optional arguments specific to `import_tar` as well as exclusion and
            common options; defaults to {}
        :type **options: Options
        :return: Output of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        import_tar_options = self.optionals.get("import_tar", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("import-tar")
        arg_list.extend(import_tar_options.parse())
        arg_list.append(archive)
        arg_list.append(tarfile)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            stats_show=import_tar_options.stats or import_tar_options.json,
            stats_json=import_tar_options.json,
            list_show=import_tar_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_import_tar, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def export_tar(
        self,
        archive: str,
        file: str,
        *paths: Optional[str],
        **options: Options,
    ) -> Output:
        """Create a tarball from an archive.

        :param archive: archive to export
        :type archive: str
        :param file: output tar file. “-” to write to stdout instead.
        :type file: str
        :param *paths: paths of items inside the archives to compare; patterns are supported
        :type *paths: Optional[str]
        :param **options: optional arguments specific to `export-tar` as well as exclusion and
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
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

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            raw_bytes=(file == "-"),
            list_show=export_tar_options.list,
            list_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(
            arg_list,
            self.archiver.do_export_tar,
            output_options=opts,
        )

        result_list = self._get_basic_results(output, opts)
        if opts.raw_bytes:
            result_list.append(("tar", output["stdout"]))

        return self._build_result(*result_list, log_json=opts.log_json)

    def serve(self, **options: Options) -> Output:
        """Start a repository server process. This command is usually not used manually.

        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        serve_options = self.optionals.to_list("serve", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("serve")
        arg_list.extend(serve_options.parse())

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_serve, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def config(
        self,
        repository: str,
        *changes: Union[str, tuple[str, str]],
        **options: Options,
    ) -> Output:
        """Get and set options in a local repository or cache config file.

        :param repository: repository to configure
        :type repository: str
        :param *changes: config key, new value
        :type *changes: Union[str, tuple[str, str]]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)
        config_options = self.optionals.get("config", options)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("config")
        arg_list.extend(config_options.parse())
        arg_list.extend(self._get_option_list(options, ExclusionOutput))
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            list_show=config_options.list,
            list_json=False,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )

        result_list = []
        if not changes:
            output = self._run(arg_list, self.archiver.do_config, output_options=opts)
            result_list.extend(self._get_basic_results(output, opts))
            if opts.list_show:
                result_list.remove(("list", ""))
                result_list.append(("list", output["stdout"]))

        change_result = []
        for change in changes:
            new_args = arg_list
            if isinstance(change, tuple):
                new_args.extend([change[0], change[1]])
            else:
                new_args.extend([change])
            output = self._run(new_args, self.archiver.do_config, output_options=opts)
            change_result.append(output["stdout"].strip())
        if change_result:
            result_list.append(("changes", change_result))

        return self._build_result(*result_list, log_json=opts.log_json)

    def with_lock(
        self,
        repository: str,
        command: str,
        *args: Union[str, int],
        **options: Options,
    ) -> Output:
        """Run a user-specified command while the repository lock is held.

        :param repository: repository to lock
        :type repository: str
        :param command: command to run
        :type command: str
        :param *args: command arguments
        :type *args: Union[str, int]
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("with-lock")
        arg_list.append(repository)
        arg_list.append(command)
        arg_list.extend(args)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_with_lock, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def break_lock(self, repository: str, **options: Options) -> Output:
        """Break the repository and cache locks.

        :param repository: repository for which to break the locks
        :type repository: str
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.append("break-lock")
        arg_list.append(repository)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_break_lock, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        return self._build_result(*result_list, log_json=opts.log_json)

    def benchmark_crud(
        self,
        repository: str,
        path: str,
        **options: Options,
    ) -> Output:
        """Benchmark borg CRUD (create, read, update, delete) operations.

        :param repository: repository to use for benchmark (must exist)
        :type repository: str
        :param path: path were to create benchmark input data
        :type path: str
        :param **options: optional arguments specific to `config` as well as
            common options; defaults to {}
        :type **options: Options
        :return: Stdout of command, None if no output created,
            dict if json flag used, str otherwise
        :rtype: Output
        """
        common_options = self._get_option(options, CommonOptions)

        arg_list = []
        arg_list.extend(common_options.parse())
        arg_list.extend(["benchmark", "crud"])
        arg_list.append(repository)
        arg_list.append(path)

        opts = OutputOptions(
            log_lvl=self._get_log_level(options),
            log_json=common_options.log_json,
            prog_show=common_options.progress,
            prog_json=common_options.log_json,
        )
        output = self._run(arg_list, self.archiver.do_benchmark_crud, output_options=opts)

        result_list = self._get_basic_results(output, opts)
        result_list.append(("benchmark", output["stdout"]))
        return self._build_result(*result_list, log_json=opts.log_json)


class BorgAPIAsync(BorgAPI):
    """Async version of the :class:`BorgAPI`."""

    CMDS = [
        "set_environ",
        "unset_environ",
        "init",
        "create",
        "extract",
        "check",
        "rename",
        "list",
        "diff",
        "delete",
        "prune",
        "compact",
        "info",
        "mount",
        "umount",
        "key_change_passphrase",
        "key_export",
        "key_import",
        "upgrade",
        "recreate",
        "import_tar",
        "export_tar",
        "serve",
        "config",
        "with_lock",
        "break_lock",
        "benchmark_crud",
    ]

    def __init__(self, *args, **kwargs):
        """Turn the commands in `:class:`BorgAPI` into async methods.

        View the `:class:`BorgAPI` for init arguments.
        """
        super().__init__(*args, **kwargs)

        for cmd in self.CMDS:
            synced = getattr(super(), cmd)
            wrapped = self._force_async(synced)
            setattr(self, cmd, wrapped)

        self.pool = ThreadPoolExecutor()

    def _force_async(self, fn):
        """Turn a sync function to async function using threads."""

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            future = self.pool.submit(fn, *args, **kwargs)
            return wrap_future(future)  # make it awaitable

        return wrapper
