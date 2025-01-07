"""Test export tar command."""

from os.path import join
from shutil import rmtree

from . import BorgapiAsyncTests, BorgapiTests


class ExportTarTests(BorgapiTests):
    """Export Tar command tests."""

    def setUp(self):
        """Prepare data for expor tar tests."""
        super().setUp()
        self._create_default()

        self.export_dir = join(self.temp, "export")
        self._make_clean(self.export_dir)
        self.tar_file = join(self.export_dir, "export.tar")

    def tearDown(self):
        """Remove data created for export tar tests."""
        rmtree(self.export_dir)
        super().tearDown()

    def test_01_basic(self):
        """Export tar file."""
        self.api.export_tar(self.archive, self.tar_file)
        self.assertFileExists(self.tar_file, "Tar file not exported")

    def test_02_stdout(self):
        """Export tar stdout."""
        output = self.api.export_tar(self.archive, "-")
        self._display("export tar 2", output)
        self.assertType(output, bytes)

    def test_03_output_json(self):
        """Export tar output."""
        output = self.api.export_tar(self.archive, self.tar_file, list=True)
        self._display("export tar 1", output)
        self.assertType(output, str)


class ExportTarAsyncTests(BorgapiAsyncTests):
    """Export Tar command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async export tar tests."""
        await super().asyncSetUp()
        await self._create_default()

        self.export_dir = join(self.temp, "export")
        self._make_clean(self.export_dir)
        self.tar_file = join(self.export_dir, "export.tar")

    def tearDown(self):
        """Remove async data created for async export tar tests."""
        rmtree(self.export_dir)
        super().tearDown()

    async def test_01_basic(self):
        """Export tar file."""
        await self.api.export_tar(self.archive, self.tar_file)
        self.assertFileExists(self.tar_file, "Tar file not exported")

    async def test_02_stdout(self):
        """Export tar stdout."""
        output = await self.api.export_tar(self.archive, "-")
        self._display("export tar 2", output)
        self.assertType(output, bytes)

    async def test_03_output_json(self):
        """Export tar output."""
        output = await self.api.export_tar(self.archive, self.tar_file, list=True)
        self._display("export tar 1", output)
        self.assertType(output, str)
