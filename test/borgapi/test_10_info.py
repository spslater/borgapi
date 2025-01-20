"""Test info command."""

from . import BorgapiAsyncTests, BorgapiTests


class InfoTests(BorgapiTests):
    """Info command tests."""

    def setUp(self):
        """Prepare data for info tests."""
        super().setUp()
        self._create_default()

    def test_01_repository(self):
        """Repository info."""
        output = self.api.info(self.repo, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyNotExists("archives", output)

    def test_02_archive(self):
        """Archive info."""
        output = self.api.info(self.archive, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyExists("archives", output)

    def test_03_repo_string(self):
        """Repo output string."""
        output = self.api.info(self.repo)
        self._display("info repo string", output)
        self.assertType(output, str)

    def test_04_repo_json(self):
        """Repo output json."""
        output = self.api.info(self.repo, json=True)
        self._display("info repo json", output)
        self.assertAnyType(output, list, dict)

        output = self.api.info(self.repo, log_json=True)
        self._display("info repo log json", output)
        self.assertType(output, str)

    def test_05_archive_string(self):
        """Archive output string."""
        output = self.api.info(self.archive)
        self._display("info archive string", output)
        self.assertType(output, str)

    def test_06_archive_json(self):
        """Archive output json."""
        output = self.api.info(self.archive, json=True)
        self._display("info archive json", output)
        self.assertAnyType(output, list, dict)


class InfoAsyncTests(BorgapiAsyncTests):
    """Info command tests."""

    async def asyncSetUp(self):
        """Prepare async data for info tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_repository(self):
        """Repository info."""
        output = await self.api.info(self.repo, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyNotExists("archives", output)

    async def test_02_archive(self):
        """Archive info."""
        output = await self.api.info(self.archive, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyExists("archives", output)

    async def test_03_repo_string(self):
        """Repo output string."""
        output = await self.api.info(self.repo)
        self._display("info repo string", output)
        self.assertType(output, str)

    async def test_04_repo_json(self):
        """Repo output json."""
        output = await self.api.info(self.repo, json=True)
        self._display("info repo json", output)
        self.assertAnyType(output, list, dict)

        output = await self.api.info(self.repo, log_json=True)
        self._display("info repo log json", output)
        self.assertType(output, str)

    async def test_05_archive_string(self):
        """Archive output string."""
        output = await self.api.info(self.archive)
        self._display("info archive string", output)
        self.assertType(output, str)

    async def test_06_archive_json(self):
        """Archive output json."""
        output = await self.api.info(self.archive, json=True)
        self._display("info archive json", output)
        self.assertAnyType(output, list, dict)
