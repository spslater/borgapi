"""Test borgapi module."""

import logging
import unittest
from os import getenv

from . import BorgapiAsyncTests, BorgapiTests


class SingleTests(BorgapiTests):
    """Simple Command and Class Methodss tests."""

    def test_01_borgapi_logger(self):
        """Verify loggers are setup correctly for borgapi."""
        loggers = logging.root.manager.loggerDict
        self.assertIn("borgapi", loggers, "borgapi logger not present")
        self.assertIn("borg", loggers, "borg logger not present")

    def test_02_set_environ(self):
        """Set new env variable."""
        key = "TEST_VARIABLE"

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        self.api.set_environ(filename=self.file_3)
        got = getenv(key)
        self.assertEqual(got, self.file_3_text)

        self.api.set_environ(dictionary={key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)

        self.api.set_environ(**{key: self.file_2_text})
        got = getenv(key)
        self.assertEqual(got, self.file_2_text)

    def test_03_unset_environ(self):
        """Remove env variable."""
        key = "TEST_VARIABLE"

        self.api.set_environ(**{key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)
        self.api.unset_environ(key)
        got = getenv(key)
        self.assertFalse(got)

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        self.api.set_environ(filename=self.file_3)
        self.api.unset_environ()
        got = getenv(key)
        self.assertFalse(got)

    @unittest.skip("WIP: Don't know what locking would be used for")
    def test_04_lock(self):
        """Don't know what locking would be used for, so don't know how to test."""


class SingleAsyncTests(BorgapiAsyncTests):
    """Simple Command and Class Methodss tests."""

    async def test_01_set_environ(self):
        """Set new env variable."""
        key = "TEST_VARIABLE"

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        await self.api.set_environ(filename=self.file_3)
        got = getenv(key)
        self.assertEqual(got, self.file_3_text)

        await self.api.set_environ(dictionary={key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)

        await self.api.set_environ(**{key: self.file_2_text})
        got = getenv(key)
        self.assertEqual(got, self.file_2_text)

    async def test_02_unset_environ(self):
        """Remove env variable."""
        key = "TEST_VARIABLE"

        await self.api.set_environ(**{key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)
        await self.api.unset_environ(key)
        got = getenv(key)
        self.assertFalse(got)

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        await self.api.set_environ(filename=self.file_3)
        await self.api.unset_environ()
        got = getenv(key)
        self.assertFalse(got)
