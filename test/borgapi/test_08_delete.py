"""Test delete command."""

import unittest

from borg.archive import Archive
from borg.repository import Repository

from . import BorgapiAsyncTests, BorgapiTests


class DeleteTests(BorgapiTests):
    """Delete command tests."""

    def test_01_repository(self):
        """Delete repository."""
        self._create_default()
        self.api.delete(self.repo)
        self.assertRaises(
            Repository.DoesNotExist,
            self.api.list,
            self.repo,
            msg="Deleted repository still exists",
        )

    # pylint: disable=invalid-name
    def test_02_repository_not_exist(self):
        """Delete repository that doesn't exist."""
        self._make_clean(self.repo)
        self.assertRaises(
            Repository.InvalidRepository,
            self.api.delete,
            self.repo,
            msg="Deleted nonexistant repository",
        )

    def test_03_archive(self):
        """Delete archive."""
        self._create_default()
        self.api.delete(self.archive)
        self.assertRaises(
            Archive.DoesNotExist,
            self.api.list,
            self.archive,
            msg="Deleted archive still exists",
        )

    def test_04_archive_not_exist(self):
        """Delete archvie that doesn't exist."""
        with self.assertLogs("borg", "WARNING") as logger:
            self.api.delete(self.archive)

        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?1.*not found",
            "Warning not logged for bad archive name",
        )

    def test_05_stats_string(self):
        """Archvie stats string."""
        self._create_default()
        output = self.api.delete(self.archive, stats=True)
        self._display("delete 1", output)
        self.assertType(output, str)

    @unittest.skip("delete has no json option for stats")
    def test_06_stats_json(self):
        """Archvie stats json."""
        self._create_default()
        output = self.api.delete(self.archive, stats=True, log_json=True)
        self._display("delete 2", output)
        self.assertType(output, list, dict)


class DeleteAsyncTests(BorgapiAsyncTests):
    """Delete command tests."""

    async def test_01_repository(self):
        """Delete repository."""
        self._create_default()
        await self.api.delete(self.repo)
        with self.assertRaises(
            Repository.DoesNotExist,
            msg="Deleted repository still exists",
        ):
            await self.api.list(self.repo)

    # pylint: disable=invalid-name
    async def test_02_repository_not_exist(self):
        """Delete repository that doesn't exist."""
        self._make_clean(self.repo)
        with self.assertRaises(
            Repository.InvalidRepository,
            msg="Deleted nonexistant repository",
        ):
            await self.api.delete(self.repo)

    async def test_03_archive(self):
        """Delete archive."""
        self._create_default()
        await self.api.delete(self.archive)
        with self.assertRaises(
            Archive.DoesNotExist,
            msg="Deleted archive still exists",
        ):
            await self.api.list(self.archive)

    async def test_04_archive_not_exist(self):
        """Delete archvie that doesn't exist."""
        with self.assertLogs("borg", "WARNING") as logger:
            await self.api.delete(self.archive)

        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?1.*not found",
            "Warning not logged for bad archive name",
        )

    async def test_05_stats_string(self):
        """Archvie stats string."""
        self._create_default()
        output = await self.api.delete(self.archive, stats=True)
        self._display("delete 1", output)
        self.assertType(output, str)

    @unittest.skip("delete has no json option for stats")
    async def test_06_stats_json(self):
        """Archvie stats json."""
        self._create_default()
        output = await self.api.delete(self.archive, stats=True, log_json=True)
        self._display("delete 2", output)
        self.assertType(output, list, dict)
