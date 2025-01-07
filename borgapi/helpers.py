"""Assortment of methods to help with debugging."""

import sys
from typing import Any, Union

__all__ = ["Json", "Output", "Options"]

Json = Union[list, dict]
Output = Union[str, Json, None]
Options = Union[bool, str, int]

ENVIRONMENT_DEFAULTS = {
    "BORG_EXIT_CODES": "modern",
    "BORG_PASSPHRASE": "",
    "BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK": "no",
    "BORG_RELOCATED_REPO_ACCESS_IS_OK": "no",
    "BORG_CHECK_I_KNOW_WHAT_I_AM_DOING": "NO",
    "BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "NO",
}


def force(*vals: Any) -> None:
    """Force print to stdout python started with."""
    out = " ".join([str(v) for v in vals])
    sys.__stdout__.write(out + "\n")
    return sys.__stdout__.flush()
