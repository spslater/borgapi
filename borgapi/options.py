"""Option Dataclasses"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Set, Union

logger = logging.getLogger(__name__)

__all__ = [
    "CommonOptions",
    "ExclusionOptions",
    "ExclusionInput",
    "ExclusionOutput",
    "FilesystemOptions",
    "ArchiveOptions",
    "ArchiveInput",
    "ArchivePattern",
    "ArchiveOutput",
    "CommandOptions",
]


@dataclass
class _DefaultField:
    """Field info in options classes"""

    name: str
    type: type
    default: object


@dataclass
class OptionsBase:
    """Holds all the shared methods for the subclasses

    Every subclass should use this __init__ method becuase it will only set the values that the
    dataclass supports and ignore the ones not part of it. This way the same options dict can be
    passed to every constructor and not have to worry about duplicating flags.
    """

    def __init__(self, **kwargs):
        default = self._defaults()
        for option in kwargs:
            if option in default:
                setattr(self, option, kwargs[option])

    @staticmethod
    def convert_name(value: str) -> str:
        """Add flag marker and replace underscores with dashes in name"""
        return "--" + value.replace("_", "-")

    def _field_set(self, field: str) -> bool:
        # pylint: disable=no-member
        default = self.__dataclass_fields__.get(field).default
        set_value = getattr(self, field)
        return set_value != default

    def _log_deprecated(self, old_field: str, new_field: str = None) -> None:
        if self._field_set(old_field):
            if new_field:
                logger.warning(
                    "[DEPRECATED] %s, use `%s` instead",
                    old_field,
                    new_field,
                )
            else:
                logger.warning("[DEPRECATED] %s, not being replaced", old_field)

    # pylint: disable=no-member
    @classmethod
    def _defaults(cls) -> Set[str]:
        defaults = set()
        for field in cls.__dataclass_fields__.values():
            defaults.add(field.name)
        return defaults

    @staticmethod
    def _is_list(type_):
        try:
            return issubclass(type_, list)
        except TypeError:
            return issubclass(type_.__origin__, list)

    def parse(self) -> List[Optional[Union[str, int]]]:
        """Turn options into list for argv

        :return: options for the command line
        :rtype: List[Optional[Union[str, int]]]
        """
        args = []
        # pylint: disable=no-member
        for key, value in self.__dataclass_fields__.items():
            attr = getattr(self, key)
            if attr is not None and value.default != attr:
                flag = self.convert_name(key)
                if value.type is bool:
                    if attr is not value.default:
                        args.append(flag)
                elif value.type is str or value.type is int:
                    args.extend([flag, attr])
                elif self._is_list(value.type):
                    for val in attr:
                        args.extend([flag, val])
                else:
                    raise TypeError(f'Unrecognized flag type for "{key}": {value.type}')
        return args


# pylint: disable=too-many-instance-attributes
@dataclass
class CommonOptions(OptionsBase):
    """Common Options for all Borg commands

    :param critical: work on log level CRITICAL
    :type critical: bool
    :param error: work on log level ERROR
    :type error: bool
    :param warning: work on log level WARNING
    :type warning: bool
    :param info: work on log level INFO
    :type info: bool
    :param verbose: work on log level INFO
    :type verbose: bool
    :param debug: work on log level DEBUG
    :type debug: bool
    :param debug_topic: enable TOPIC debugging (can be specified multiple times). The logger path
        is borg.debug.<TOPIC> if TOPIC is not fully qualified.
    :type debug_topic: List[str]
    :param progress: show progress information
    :type progress: bool
    :param log_json: output one JSON object per log line instead of formatted text.
    :type log_json: bool
    :param lock_wait: wait at most SECONDS for acquiring a repository/cache lock (default: 1).
    :type lock_wait: int
    :param bypass_lock: bypass locking mechanism
    :type bypass_lock: bool
    :param show_version: show/log the borg version
    :type show_version: bool
    :param show_rc: show/log the return code (rc)
    :type show_rc: bool
    :param umask: set umask to M (local and remote, default: 0077)
    :type umask: str
    :param remote_path: use PATH as borg executable on the remote (default: “borg”)
    :type remote_path: str
    :param remote_ratelimit: set remote network upload rate limit in kiByte/s (default: 0=unlimited)
    :type remote_ratelimit: int
    :param consider_part_files: treat part files like normal files (e.g. to list/extract them)
    :type consider_part_files: bool
    :param debug_profile: write execution profile in Borg format into FILE. For local use a
        Python-compatible file can be generated by suffixing FILE with “.pyprof”
    :type debug_profile: str
    :param rsh: Use this command to connect to the ‘borg serve’ process (default: ‘ssh’)
    :type rsh: str
    """

    critical: bool = False
    error: bool = False
    warning: bool = False
    info: bool = False
    verbose: bool = False
    debug: bool = False
    debug_topic: List[str] = None
    progress: bool = False
    log_json: bool = False
    lock_wait: int = None
    bypass_lock: bool = False
    show_version: bool = False
    show_rc: bool = False
    umask: str = None
    remote_path: str = None
    remote_ratelimit: int = None
    consider_part_files: bool = False
    debug_profile: str = None
    rsh: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.debug_topic, str):
            self.exclude = [self.exclude]
        if self.umask and not re.match(r"^[0-9]{4}", self.umask):
            raise ValueError("umask must be in format 0000 permission code, eg: 0077")


@dataclass
class ExclusionOptions(OptionsBase):
    """Options for excluding various files from backup

    :param exclude: exclude paths matching PATTERN
    :type exclude: List[str]
    :param exclude_from: read exclude patterns from EXCLUDEFILE, one per line
    :type exclude_from: str
    :param pattern: include/exclude paths matching PATTERN (experimental)
    :type pattern: str
    :param patterns_from: read include/exclude patterns from PATTERNFILE, one per
        line (experimental)
    :type patterns_from: str
    """

    exclude: List[str] = None
    exclude_from: str = None
    pattern: List[str] = None
    patterns_from: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.exclude, str):
            self.exclude = [self.exclude]
        if isinstance(self.pattern, str):
            self.pattern = [self.pattern]


@dataclass
class ExclusionInput(ExclusionOptions):
    """Exclusion Options when inputing data to the archive

    :param exclude_caches: exclude directories that contain a CACHEDIR.TAG file
        (http://www.bford.info/cachedir/spec.html)
    :type exclude_caches: bool
    :param exclude_if_present: exclude directories that are tagged by containing a filesystem
        object with the given NAME
    :type exclude_if_present: List[str]
    :param keep_exclude_tags: if tag objects are specified with --exclude-if-present, don’t omit
        the tag objects themselves from the backup archive
    :type keep_exclude_tags: bool
    :param keep_tag_files: alternate to keep_exclude_tags
    :type keep_tag_files: bool
    :param exclude_nodump: exclude files flagged NODUMP
    :type exclude_nodump: bool
    """

    exclude_caches: bool = False
    exclude_if_present: List[str] = None
    keep_exclude_tags: bool = False
    keep_tag_files: bool = False
    exclude_nodump: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.exclude_if_present, str):
            self.exclude_if_present = [self.exclude_if_present]


@dataclass
class ExclusionOutput(ExclusionOptions):
    """Exclusion Options when outputing data in the archive

    :param strip_componts: Remove the specified number of leading path elements. Paths with fewer
        elements will be silently skipped
    :type strip_componts: int
    """

    strip_componts: int = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class FilesystemOptions(OptionsBase):
    """Options for how to handle filesystem attributes

    :param one_file_system: stay in the same file system and do not store mount points of other
        file systems. This might behave different from your expectations, see the docs.
    :type one_file_system: bool
    :param numeric_owner: only store numeric user and group identifiers
    :type numeric_owner: bool
    :param noatime: do not store atime into archive
    :type noatime: bool
    :param noctime: do not store ctime into archive
    :type noctime: bool
    :param nobirthtime: do not store birthtime (creation date) into archive
    :type nobirthtime: bool
    :param nobsdflags: do not read and store bsdflags (e.g. NODUMP, IMMUTABLE) into archive
    :type nobsdflags: bool
    :param noacls: do not read and store ACLs into archive
    :type noacls: bool
    :param noxattrs: do not read and store xattrs into archive
    :type noxattrs: bool
    :param ignore_inode: ignore inode data in the file metadata cache used to detect
        unchanged files.
    :type ignore_inode: bool
    :param files_cache: operate files cache in MODE. default: ctime,size,inode
    :type files_cache: str
    :param read_special: open and read block and char device files as well as FIFOs as if they were
        regular files. Also follows symlinks pointing to these kinds of files.
    :type read_special: bool
    """

    one_file_system: bool = False
    numeric_owner: bool = False
    noatime: bool = False
    noctime: bool = False
    nobirthtime: bool = False
    nobsdflags: bool = False
    noacls: bool = False
    noxattrs: bool = False
    ignore_inode: bool = False
    files_cache: str = None
    read_special: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ArchiveOptions(OptionsBase):
    """Options related to the archive"""

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ArchiveInput(ArchiveOptions):
    """Archive Options when inputing data to the archive

    :param comment: add a comment text to the archive
    :type comment: str
    :param timestamp: manually specify the archive creation date/time
        (UTC, yyyy-mm-ddThh:mm:ss format). Alternatively, give a reference file/directory.
    :type timestamp: str
    :param checkpoint_interval: write checkpoint every SECONDS seconds (Default: 1800)
    :type checkpoint_interval: int
    :param chunker_params: specify the chunker parameters (CHUNK_MIN_EXP, CHUNK_MAX_EXP,
        HASH_MASK_BITS, HASH_WINDOW_SIZE). default: 19,23,21,4095
    :type chunker_params: str
    :param compression: select compression algorithm, see the output of the “borg help compression”
        command for details.
    :type compression: str
    """

    comment: str = None
    timestamp: str = None
    checkpoint_interval: int = None
    chunker_params: str = None
    compression: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ArchivePattern(ArchiveOptions):
    """Archive Options when outputing data in the archive

    :param prefix: only consider archive names starting with this prefix.
    :type prefix: str
    :param glob_archives: only consider archive names matching the glob.
        sh: rules apply, see “borg help patterns”. --prefix and --glob-archives
        are mutually exclusive.
    :type glob_archives: str
    """

    prefix: str = None
    glob_archives: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ArchiveOutput(ArchivePattern):
    """Archive options when filtering output

    :param sort_by: Comma-separated list of sorting keys; valid keys are: timestamp, name, id;
        default is: timestamp
    :type sort_by: str
    :param first: consider first N archives after other filters were applied
    :type first: int
    :param last: consider last N archives after other filters were applied
    :type last: int
    """

    sort_by: str = None
    first: int = None
    last: int = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class InitOptional(OptionsBase):
    """Init command options

    :param append_only: create an append-only mode repository
    :type append_only: bool
    :param storage_quota: set storage quota of the new repository (e.g. 5G, 1.5T)
        borg default: no quota
    :type storage_quota: str
    :param make_parent_dirs: create the parent directories of the repository
        directory, if they are missing
    :type make_parent_dirs: bool
    """

    append_only: bool = False
    storage_quota: str = None
    make_parent_dirs: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# pylint: disable=too-many-instance-attributes
@dataclass
class CreateOptional(OptionsBase):
    """Create command options

    :param dry_run: do not create a backup archive
    :type dry_run: bool
    :param stats: print statistics for the created archive
    :type stats: bool
    :param list: output verbose list of items (files, dirs, …)
    :type list: bool
    :param filter: only display items with the given status characters
    :type filter: str
    :param json: output stats as JSON. Implies `stats`
    :type json: bool
    :param no_cache_sync: experimental: do not synchronize the cache.
        Implies not using the files cache
    :type no_cache_sync: bool
    :param no_files_cache: do not load/update the file metadata cache
        used to detect unchanged files
    :type no_files_cache: bool
    :param stdin_name: use NAME in archive for stdin data
        borg default: “stdin”
    :type stdin_name: str
    :param stdin_user: set user USER in archive for stdin data
        borg default: "root"
    :type stdin_user: str
    :param stdin_group: set group GROUP in archive for stdin data
        borg default: "root"
    :type stdin_group: str
    :param stdin_mode: set mode to M in archive for stdin data
        borg default: 0660
    :type stdin_mode: str
    """

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


@dataclass
class ExtractOptional(OptionsBase):
    """Extract command options

    :param list: output verbose list of items (files, dirs, …)
    :type list: bool
    :param dry_run: do not actually change any files
    :type dry_run: bool
    :param numeric_owner: only obey numeric user and group identifiers
    :type numeric_owner: bool
    :param nobsdflags: do not extract/set bsdflags (e.g. NODUMP, IMMUTABLE)
    :type nobsdflags: bool
    :param noacls: do not extract/set ACLs
    :type noacls: bool
    :param noxattrs: do not extract/set xattrs
    :type noxattrs: bool
    :param stdout: write all extracted data to stdout
    :type stdout: bool
    :param sparse: create holes in output sparse file from all-zero chunks
    :type sparse: bool
    """

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


@dataclass
class CheckOptional(OptionsBase):
    """Check command options

    :param repository_only: only perform repository checks
    :type repository_only: bool
    :param archives_only: only perform archives checks
    :type archives_only: bool
    :param verify_data: perform cryptographic archive data integrity
        verification conflicts with `repository_only`
    :type verify_data: bool
    :param repair: attempt to repair any inconsistencies found
    :type repair: bool
    :param save_space: work slower, but using less space
    :type save_space: bool
    """

    repository_only: bool = False
    archives_only: bool = False
    verify_data: bool = False
    repair: bool = False
    save_space: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ListOptional(OptionsBase):
    """List command options

    :param short: only print file/directory names, nothing else
    :type short: bool
    :param format: specify format for file listing
        borg default: “{mode} {user:6} {group:6} {size:8d} {mtime} {path}{extra}{NL}”
    :type format: str
    :param json: only valid for listing repository contents. Format output as JSON.
        The form of `format` is ignored, but keys used in it are added to the JSON output.
        Some keys are always present. Note: JSON can only represent text.
        A “barchive” key is therefore not available.
    :type json: bool
    :param json_lines: only valid for listing archive contents. Format output as JSON lines.
        The form of `format` is ignored, but keys used in it are added to the JSON output.
        Some keys are always present. Note: JSON can only represent text.
        A “bpath” key is therefore not available.
    :type json_lines: bool
    """

    short: bool = False
    format: str = None
    json: bool = False
    json_lines: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class DiffOptional(OptionsBase):
    """Diff command options

    :param numeric_owner: only consider numeric user and group identifiers
    :type numeric_owner: bool
    :param same_chunker_params: override check of chunker parameters
    :type same_chunker_params: bool
    :param sort: srt the output lines by file path
    :type sort: bool
    :param json_lines: format output as JSON lines
    :type json_lines: bool
    """

    numeric_owner: bool = False
    same_chunker_params: bool = False
    sort: bool = False
    json_lines: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._log_deprecated("numeric_owner", "numeric_ids")


@dataclass
class DeleteOptional(OptionsBase):
    """Delete command options

    :param dry_run: do not change repository
    :type dry_run: bool
    :param stats: print statistics for the deleted archive
    :type stats: bool
    :param cache_only: delete only the local cache for the given repository
    :type cache_only: bool
    :param force: force deletion of corrupted archives
    :type force: bool
    :param save_space: work slower, but using less space
    :type save_space: bool
    """

    dry_run: bool = False
    stats: bool = False
    cache_only: bool = False
    force: bool = False
    save_space: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# pylint: disable=too-many-instance-attributes
@dataclass
class PruneOptional(OptionsBase):
    """Prune command options

    :param dry_run: do not change repository
    :type dry_run: bool
    :param force: force pruning of corrupted archives
    :type force: bool
    :param stats: print statistics for the deleted archive
    :type stats: bool
    :param list: output verbose list of archives it keeps/prunes
    :type list: bool
    :param keep_within: keep all archives within this time interval
    :type keep_within: str
    :param keep_last: number of secondly archives to keep
    :type keep_last: int
    :param keep_secondly: number of secondly archives to keep
    :type keep_secondly: int
    :param keep_minutely: number of minutely archives to keep
    :type keep_minutely: int
    :param keep_hourly: number of hourly archives to keep
    :type keep_hourly: int
    :param keep_daily: number of daily archives to keep
    :type keep_daily: int
    :param keep_weekly: number of weekly archives to keep
    :type keep_weekly: int
    :param keep_monthly: number of monthly archives to keep
    :type keep_monthly: int
    :param keep_yearly: number of yearly archives to keep
    :type keep_yearly: int
    :param save_space: work slower, but using less space
    :type save_space: bool
    """

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


@dataclass
class InfoOptional(OptionsBase):
    """Info command options

    :param json: format output as JSON
    :type json: bool
    """

    json: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# pylint: disable=invalid-name
@dataclass
class MountOptional(OptionsBase):
    """Mount command options

    :param foreground: stay in foreground, do not daemonize
    :type foreground: bool
    :param o: extra mount options
    :type o: str
    """

    foreground: bool = True
    o: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class KeyExportOptional(OptionsBase):
    """Key Export command options

    :param paper: create an export suitable for printing and later type-in
    :type paper: bool
    :param qr_html: create an html file suitable for printing and later type-in or qr scan
    :type qr_html: bool
    """

    paper: bool = False
    qr_html: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class KeyImportOptional(OptionsBase):
    """Key Import command options

    :param paper: interactively import from a backup done with `paper`
    :type paper: bool
    """

    paper: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class UpgradeOptional(OptionsBase):
    """Upgrade command options

    :param dry_run: do not change repository
    :type dry_run: bool
    :param inplace: rewrite repository in place, with no chance of going
        back to older versions of the repository
    :type inplace: bool
    :param force: force upgrade
    :type force: bool
    :param tam: enable manifest authentication (in key and cache)
    :type tam: bool
    :param disable_tam: disable manifest authentication (in key and cache)
    :type disable_tam: bool
    """

    dry_run: bool = False
    inplace: bool = False
    force: bool = False
    tam: bool = False
    disable_tam: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ExportTarOptional(OptionsBase):
    """Export Tar command options

    :param tar_filter: filter program to pipe data through
    :type tar_filter: str
    :param list: output verbose list of items (files, dirs, …)
    :type list: bool
    """

    tar_filter: str = None
    list: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ServeOptional(OptionsBase):
    """Serve command options

    :param restrict_to_path: restrict repository access to PATH.
        Can be specified multiple times to allow the client access to several directories.
        Access to all sub-directories is granted implicitly;
        PATH doesn’t need to directly point to a repository
    :type restrict_to_path: str
    :param restrict_to_repository: restrict repository access.
        Only the repository located at PATH (no sub-directories are considered) is accessible.
        Can be specified multiple times to allow the client access to several repositories.
        Unlike `restrict_to_path` sub-directories are not accessible;
        PATH needs to directly point at a repository location.
        PATH may be an empty directory or the last element of PATH may not exist,
        in which case the client may initialize a repository there
    :type restrict_to_repository: str
    :param append_only: only allow appending to repository segment files
    :type append_only: bool
    :param storage_quota: Override storage quota of the repository (e.g. 5G, 1.5T).
        When a new repository is initialized, sets the storage quota on the new repository as well.
        borg default: no quota
    :type storage_quota: str
    """

    restrict_to_path: str = None
    restrict_to_repository: str = None
    append_only: bool = False
    storage_quota: str = None

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@dataclass
class ConfigOptional(OptionsBase):
    """Config command options

    :param cache: get and set values from the repo cache
    :type cache: bool
    :param delete: delete the key from the config file
    :type delete: bool
    :param list: list the configuration of the repo
    :type list: bool
    """

    cache: bool = False
    delete: bool = False
    list: bool = False

    # pylint: disable=useless-super-delegation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CommandOptions:
    """Optional Arguments for the different commands"""

    optional_classes = {
        "init": InitOptional,
        "create": CreateOptional,
        "extract": ExtractOptional,
        "check": CheckOptional,
        "list": ListOptional,
        "diff": DiffOptional,
        "delete": DeleteOptional,
        "prune": PruneOptional,
        "info": InfoOptional,
        "mount": MountOptional,
        "key_export": KeyExportOptional,
        "key_import": KeyImportOptional,
        "upgrade": UpgradeOptional,
        "export_tar": ExportTarOptional,
        "serve": ServeOptional,
        "config": ConfigOptional,
    }

    def __init__(self, defaults: dict = None):
        self.defaults = defaults or {}

    @classmethod
    def _get_optional(cls, command: str) -> OptionsBase:
        try:
            return cls.optional_classes[command]
        except KeyError as e:
            raise ValueError(
                f"Command `{command}` does not have any optional arguments or does not exist."
            ) from e

    def get(self, command: str, values: dict) -> OptionsBase:
        """Return OptionsBase with flags set for `command`

        :param command: command being called
        :type command: str
        :param values: dictionary with values for flags
        :type values: dict
        :return: instance of command dataclass
        :rtype: OptionsBase
        """

        optionals = {**self.defaults.get(command, {}), **(values or {})}
        return self._get_optional(command)(**optionals)

    def to_list(self, command: str, values: dict) -> list:
        """Parsed args list for command

        :param command: command name
        :type command: str
        :param values: options flags
        :type values: dict
        :return: list of converted flags
        :rtype: list
        """
        return self.get(command, values).parse()
