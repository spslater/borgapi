"""Test list command."""

from . import BorgapiAsyncTests, BorgapiTests


class ListTests(BorgapiTests):
    """List command tests."""

    def setUp(self):
        """Prepare data for list tests."""
        super().setUp()
        self._create_default()

    def test_01_basic(self):
        """List repo archvies and archive files."""
        output = self.api.list(self.repo, json=True)
        num_archvies = len(output["archives"])
        self.assertEqual(num_archvies, 1, "Unexpected number of archives returned")

        output = self.api.list(self.archive, json_lines=True)
        num_files = len(output)
        self.assertEqual(num_files, 3, "Unexpected number of files returned")

    def test_02_repo_basic(self):
        """List repo."""
        output = self.api.list(self.repo)
        self._display("list repo", output)
        self.assertType(output, str)

    def test_03_repo_short(self):
        """List repo short."""
        output = self.api.list(self.repo, short=True)
        self._display("list repo short", output)
        self.assertType(output, str)

    def test_04_repo_json(self):
        """List repo json."""
        output = self.api.list(self.repo, json=True)
        self._display("list repo json", output)
        self.assertAnyType(output, list, dict)
        output = self.api.list(self.repo, log_json=True)
        self._display("list repo log json", output)
        self.assertAnyType(output, str)

    def test_05_archive_basic(self):
        """List archive."""
        output = self.api.list(self.archive)
        self._display("list archive", output)
        self.assertType(output, str)

    def test_06_archive_short(self):
        """List archive short."""
        output = self.api.list(self.archive, short=True)
        self._display("list archive short", output)
        self.assertType(output, str)

    def test_07_archive_json(self):
        """List archive json."""
        output = self.api.list(self.archive, json_lines=True)
        self._display("list archive json", output)
        self.assertAnyType(output, list, dict)


class ListAsyncTests(BorgapiAsyncTests):
    """List command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async list tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_basic(self):
        """List repo archvies and archive files."""
        output = await self.api.list(self.repo, json=True)
        num_archvies = len(output["archives"])
        self.assertEqual(num_archvies, 1, "Unexpected number of archives returned")

        output = await self.api.list(self.archive, json_lines=True)
        num_files = len(output)
        self.assertEqual(num_files, 3, "Unexpected number of files returned")

    async def test_02_repo_basic(self):
        """List repo."""
        output = await self.api.list(self.repo)
        self._display("list repo", output)
        self.assertType(output, str)

    async def test_03_repo_short(self):
        """List repo short."""
        output = await self.api.list(self.repo, short=True)
        self._display("list repo short", output)
        self.assertType(output, str)

    async def test_04_repo_json(self):
        """List repo json."""
        output = await self.api.list(self.repo, json=True)
        self._display("list repo json", output)
        self.assertAnyType(output, list, dict)
        output = await self.api.list(self.repo, log_json=True)
        self._display("list repo log json", output)
        self.assertAnyType(output, str)

    async def test_05_archive_basic(self):
        """List archive."""
        output = await self.api.list(self.archive)
        self._display("list archive", output)
        self.assertType(output, str)

    async def test_06_archive_short(self):
        """List archive short."""
        output = await self.api.list(self.archive, short=True)
        self._display("list archive short", output)
        self.assertType(output, str)

    async def test_07_archive_json(self):
        """List archive json."""
        output = await self.api.list(self.archive, json_lines=True)
        self._display("list archive json", output)
        self.assertAnyType(output, list, dict)
