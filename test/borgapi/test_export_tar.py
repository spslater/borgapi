"""Test export tar command"""
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class ExportTarTests(BorgapiTests):
    """Export Tar command tests"""

    def test_export_tar(self):
        """Export tar file"""
        api = self._init_and_create(self.repo, "1", self.data)

        export_dir = join(self.temp, "export")
        self._make_clean(export_dir)
        tar_file = join(export_dir, "export.tar")

        api.export_tar(f"{self.repo}::1", tar_file)
        self.assertFileExists(tar_file, "Tar file not exported")

        rmtree(export_dir)

    def test_export_tar_stdout(self):
        """Export tar file"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.export_tar(f"{self.repo}::1", "-")
        self.assertTrue(out, "Exported tar contains no bytes exported")
