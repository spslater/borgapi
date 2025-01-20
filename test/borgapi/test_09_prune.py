"""Test prune command."""

from os import remove
from time import sleep

from . import BorgapiAsyncTests, BorgapiTests


class PruneTests(BorgapiTests):
    """Prune command tests."""

    def setUp(self):
        """Prepare data for async tests."""
        super().setUp()
        self._create_default()
        sleep(1)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        sleep(1)
        remove(self.file_1)
        self.api.create(f"{self.repo}::3", self.data)
        sleep(1)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_1_text)
        self.api.create(f"{self.repo}::4", self.data)
        sleep(1)
        remove(self.file_2)
        self.api.create(f"{self.repo}::5", self.data)
        sleep(1)

    # pylint: disable=invalid-sequence-index
    def test_01_basic(self):
        """Prune archives."""
        self.api.prune(self.repo, keep_last="3")
        output = self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 3, "Unexpected number of archvies pruned")

    def test_02_output_list(self):
        """Prune output list."""
        output = self.api.prune(self.repo, keep_last="3", dry_run=True, list=True)
        self._display("prune list", output)
        self.assertType(output, str)

    def test_03_output_stats(self):
        """Prune output stats."""
        output = self.api.prune(self.repo, keep_last="3", dry_run=True, stats=True)
        self._display("prune stats", output)
        self.assertType(output, str)


class PruneAsyncTests(BorgapiAsyncTests):
    """Prune command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async prune tests."""
        await super().asyncSetUp()
        await self._create_default()
        sleep(1)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        await self.api.create(f"{self.repo}::2", self.data)
        sleep(1)
        remove(self.file_1)
        await self.api.create(f"{self.repo}::3", self.data)
        sleep(1)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_1_text)
        await self.api.create(f"{self.repo}::4", self.data)
        sleep(1)
        remove(self.file_2)
        await self.api.create(f"{self.repo}::5", self.data)
        sleep(1)

    # pylint: disable=invalid-sequence-index
    async def test_01_basic(self):
        """Prune archives."""
        await self.api.prune(self.repo, keep_last="3")
        output = await self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 3, "Unexpected number of archvies pruned")

    async def test_02_output_list(self):
        """Prune output list."""
        output = await self.api.prune(self.repo, keep_last="3", dry_run=True, list=True)
        self._display("prune list", output)
        self.assertType(output, str)

    async def test_03_output_stats(self):
        """Prune output stats."""
        output = await self.api.prune(self.repo, keep_last="3", dry_run=True, stats=True)
        self._display("prune stats", output)
        self.assertType(output, str)
