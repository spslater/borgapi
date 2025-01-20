"""Save Borg output to review after command call."""

import logging
import sys
from dataclasses import dataclass
from io import BytesIO, StringIO, TextIOWrapper
from types import TracebackType
from typing import Optional, Union

try:
    from typing import Self
except ImportError:
    # Self isn't added to the typing library until version 3.11
    from typing import TypeVar

    Self = TypeVar("Self", bound="OutputCapture")

from borg.logger import JsonFormatter

from .helpers import Json

__all__ = ["OutputOptions", "ListStringIO", "PersistantHandler", "BorgLogCapture", "OutputCapture"]

LOG_LVL = "warning"


@dataclass
class OutputOptions:
    """Settings for what output should be saved."""

    raw_bytes: bool = False
    log_lvl: str = LOG_LVL
    log_json: bool = False
    list_show: bool = False
    list_json: bool = False
    stats_show: bool = False
    stats_json: bool = False
    repo_show: bool = False
    repo_json: bool = False
    prog_show: bool = False
    prog_json: bool = False


class ListStringIO(StringIO):
    """Save TextIO to a list of single lines."""

    def __init__(self, initial_value="", newline="\n"):
        r"""Wrap StringIO to gobble written data and save to a list.

        :param initial_value: Initial value of buffer, passed to StringIO, defaults to ''
        :type initial_value: str, optional
        :param newline: What character to use for newlines, passed to StringIO, defaults to '\\n'
        :type newline: str, optional
        """
        super().__init__(initial_value=initial_value, newline=newline)
        self.values = list()
        self.idx = 0

    def write(self, s: str, /):
        """Gobble written data and save it to a list right away.

        :param s: data to write to output
        :type s: str
        """
        super().write(s)
        self.flush()
        val = self.getvalue()
        self.seek(0)
        self.truncate()
        dvals = val.replace("\r", "\n").splitlines(keepends=True)
        vals = []
        for v in dvals:
            nv = v.rstrip()
            if v[-1] == "\n":
                nv = f"{nv}\n"
            if nv:
                vals.append(nv)
        if vals and self.values and self.values[-1][-1] != "\n":
            self.values[-1] = self.values[-1] + vals[0]
            self.values.extend(vals[1:])
        else:
            self.values.extend(vals)

    def get(self) -> str:
        """Get next line of output data.

        :return: Next line of output, None if end of list
            and no new lines
        :rtype: str
        """
        if self.idx >= len(self.values):
            return None
        rec = self.values[self.idx]
        self.idx += 1
        return rec

    def get_all(self) -> list[str]:
        """Get all data that has been written so far.

        :return: all lines written to output split on newlines
        :rtype: list[str]
        """
        return self.values


class PersistantHandler(logging.Handler):
    """Save logged information into a list of records."""

    def __init__(self, json: bool = False):
        """Prep handler to be attached to a :class:`logging.Logger`.

        :param json: if the output should be saved as a json value
            instead of a string, defaults to False
        :type json: bool, optional
        """
        super().__init__()
        self.records = list()
        self.idx = 0
        self.closed = False

        self.json = json

        fmt = "%(message)s"
        formatter = JsonFormatter(fmt) if json else logging.Formatter(fmt)
        self.setFormatter(formatter)
        self.setLevel("INFO")

    def emit(self, record: logging.LogRecord):
        """Log the record to the handlers internal list.

        Implements `logger.Handler.emit`. Should not be manually called.

        :param record: Logging record to be saved to the list.
        :type record: logging.LogRecord
        """
        try:
            formatted = self.format(record)
            if not self.json:
                formatted = formatted.rstrip()
            if formatted:
                self.records.append(formatted)
        except Exception:
            self.handleError(record)

    def get(self) -> Union[str, Json]:
        """Retrieve the next record in the list.

        :return: Next item in the list if there is one available, otherwise `None`
        :rtype: Union[str, Json, None]
        """
        if self.idx >= len(self.records):
            return None
        rec = self.records[self.idx]
        self.idx += 1
        return rec

    def get_all(self) -> list[Union[str, Json]]:
        """Retrieve full list of records.

        :return: _description_
        :rtype: list[Union[str, Json]]
        """
        return self.records

    def get_rest(self) -> list[Union[str, Json]]:
        """Retrieve remaining records starting at current index.

        :return: Unretrieved records in the list
        :rtype: list[Union[str, Json]]
        """
        if self.idx < len(self.records):
            return self.records[self.idx :]
        return []

    def __str__(self):
        """Join every record saved with newlines.

        :return: String of the records saved.
        :rtype: str
        """
        return "\n".join([str(r) for r in self.records])

    def value(self):
        """Return the records based on the output type (json or string).

        :return: All records in pretty-ish format
        :rtype: Union[str, list[Json]]
        """
        if self.json:
            return self.records
        return str(self)

    def close(self):
        """Set a flag to know if any new records should be expected.

        When `self.closed` is `True`, then no new records will be written
        to the logger.
        """
        self.closed = True

    def seek(self, idx: int = 0):
        """Set the index for getting the next record.

        Writing records always go to the end of the list.

        :param idx: position to start getting records from next, defaults to 0
        :type idx: int, optional
        """
        self.idx = idx


class BorgLogCapture:
    """Capture Borgs output to review after a command call."""

    def __init__(self, logger: str, log_json: bool = False):
        """Attach handler to specified logger to gather output data.

        :param logger: Logger to get information from.
        :type logger: str
        :param log_json: save data as a json instead of a string, defaults to False
        :type log_json: bool, optional
        """
        self.logger = logging.getLogger(logger)
        self.handler = PersistantHandler(log_json)
        self.logger.addHandler(self.handler)

    def get(self) -> Optional[Union[str, Json]]:
        """Get next value in the handler.

        :return: Next value to read from the handler if it exists.
            Otherwise will return None.
        :rtype: Optional[str]
        """
        return self.handler.get()

    def get_all(self) -> list[Union[str, Json]]:
        """Get every logged record since the handler was attached.

        :return: list of each record entry
        :rtype: list
        """
        return self.handler.get_all()

    def value(self):
        """Get full data from handler.

        :return: the full output of the data
        :rtype: str or dict
        """
        return self.handler.value()

    def close(self):
        """Close handler and remove it from logger."""
        self.handler.close()
        self.logger.removeHandler(self.handler)

    def __str__(self):
        """Join all lines together as single string block.

        :return: String of all data logged to handler
        :rtype: str
        """
        return "\n".join(self.get_all())


class OutputCapture:
    """Capture stdout and stderr by redirecting to inmemory streams.

    :param raw: Expecting raw bytes from stdout and stderr
    :type raw: bool
    """

    def __init__(self):
        """Create object to log Borg output."""
        self.ready = False

    def __call__(self, opts: OutputOptions) -> Self:
        """Create handlers to use by a context manager.

        Clears out old handlers from previous calls and creates new
        ones for next Borg command to be used.

        :param opts: Display options
        :type opts: OutputOptions
        :return: After setup, the object needs to be pased to the context manager.
        :rtype: Self
        """
        self.ready = False
        self.opts = opts
        self.raw = self.opts.raw_bytes
        self._init_stdout(self.raw)
        self._init_stderr()

        self.list_capture = None
        if self.opts.list_show:
            self.list_capture = BorgLogCapture("borg.output.list", self.opts.list_json)

        self.stats_capture = None
        if self.opts.stats_show:
            self.stats_capture = BorgLogCapture("borg.output.stats", self.opts.stats_json)

        self.repo_capture = None
        if self.opts.repo_show:
            self.repo_capture = BorgLogCapture("borg.repository", self.opts.repo_json)

        self.ready = True

        return self

    def _init_stdout(self, raw: bool):
        self._stdout = TextIOWrapper(BytesIO()) if raw else ListStringIO()
        self.stdout_original = sys.stdout
        sys.stdout = self._stdout

    def _init_stderr(self):
        self._stderr = ListStringIO()
        self.stderr_original = sys.stderr
        sys.stderr = self._stderr

    def getvalues(self) -> Union[str, bytes]:
        """Get the captured values from the redirected stdout and stderr.

        :return: Redirected values from stdout and stderr
        :rtype: Union[str, bytes]
        """
        output = {}

        if self.raw:
            stdout_value = self._stdout.buffer.getvalue()
        else:
            stdout_value = "".join(self._stdout.get_all())
        output["stdout"] = stdout_value
        output["stderr"] = "".join(self._stderr.get_all())

        if self.opts.list_show:
            output["list"] = self.list_capture.value()
        if self.opts.stats_show:
            output["stats"] = self.stats_capture.value()
        if self.opts.repo_show:
            output["repo"] = self.repo_capture.value()

        return output

    def close(self):
        """Close the underlying IO streams and reset stdout and stderr."""
        try:
            if not self.raw:
                self._stdout.close()
            self._stderr.close()
            if self.list_capture:
                self.list_capture.close()
            if self.stats_capture:
                self.stats_capture.close()
            if self.repo_capture:
                self.repo_capture.close()
        finally:
            sys.stdout = self.stdout_original
            sys.stderr = self.stderr_original
            self.ready = False

    def __enter__(self) -> Self:
        """Return the runtime context.

        No additional work needs to be done when entering a context.

        :return: Get `self` to use in a context
        :rtype: Self
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Cleanup the capture when finished with a `with` context.

        Don't want to hide any exceptions during the context, so a return
        value of `True`

        :param exc_type: exception type
        :type exc_type: Optional[type[BaseException]]
        :param exc_value: exception that was raised
        :type exc_value: Optional[BaseException]
        :param traceback: traceback of the exception that was raised
        :type traceback: Optional[TracebackType]
        :return: Propogates any exception that happens during runtime.
        :rtype: bool
        """
        self.close()
        return False

    def list(self):
        """Get buffer where list information is being logged."""
        return self.list_capture

    def stats(self):
        """Get buffer where stats are being logged."""
        return self.stats_capture

    def repository(self):
        """Get buffer where repository info is being logged."""
        return self.repo_capture

    def progress(self):
        """Get buffer where progress is being logged."""
        return self._stderr

    def stdout(self):
        """Get buffer stdout is being logged."""
        return self._stdout.buffer if self.raw else self._stdout

    def stderr(self):
        """Get buffer stderr is being logged."""
        return self._stderr
