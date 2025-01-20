"""Test deff command."""

from . import BorgapiAsyncTests, BorgapiTests


class ProgressTests(BorgapiTests):
    """Compact command tests."""

    def setUp(self):
        """Prepare data for progress tests."""
        super().setUp()
        self._create_default()

    def test_01_output(self):
        """Compact with progress."""
        output = self.api.create(f"{self.repo}::2", self.data, progress=True)
        self._display("compact with progress", output)
        self.assertNotNone(output)
        self.assertGreater(len(output), 0)


class ProgressAsyncTests(BorgapiAsyncTests):
    """Compact command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async progress tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_output(self):
        """Compact with progress."""
        output = await self.api.create(f"{self.repo}::2", self.data, progress=True)
        self._display("compact with progress", output)
        self.assertNotNone(output)
        self.assertGreater(len(output), 0)

    async def test_02_watching(self):
        """Capture progress before compacting is done."""
        output = self.api.create(f"{self.repo}::2", self.data, progress=True, log_json=True)
        test = self.api.output.progress().get()
        while test is None:
            test = self.api.output.progress().get()
        await output
        self._display("stream", test)
        self.assertNotNone(test)
        self.assertGreater(len(test), 0)
