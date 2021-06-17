"""Test export tar command"""
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class ExportTarTests(BorgapiTests):
    """Export Tar command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

        self.export_dir = join(self.temp, "export")
        self._make_clean(self.export_dir)
        self.tar_file = join(self.export_dir, "export.tar")

    def tearDown(self):
        rmtree(self.export_dir)
        super().tearDown()

    def test_basic(self):
        """Export tar file"""
        self.api.export_tar(self.archive, self.tar_file)
        self.assertFileExists(self.tar_file, "Tar file not exported")

    def test_stdout(self):
        """Export tar stdout"""
        output = self.api.export_tar(self.archive, "-")
        self._display("export tar 2", output)
        self.assertType(output, bytes)

    def test_output_json(self):
        """Export tar output"""
        output = self.api.export_tar(self.archive, self.tar_file, list=True)
        self._display("export tar 1", output)
        self.assertType(output, str)
