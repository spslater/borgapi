"""Test export tar command."""

import sys
from io import BytesIO, TextIOWrapper
from os import getenv
from os.path import join
from shutil import rmtree

from borg.archive import Archive

from . import BorgapiAsyncTests, BorgapiTests


class ImportTarTests(BorgapiTests):
    """Import Tar command tests."""

    def setUp(self):
        """Prepare data for expor tar tests."""
        super().setUp()
        self._create_default()

        self.export_dir = join(self.temp, "export")
        self._make_clean(self.export_dir)
        self.tar_file = join(self.export_dir, "export.tar")

    def tearDown(self):
        """Remove data created for export tar tests."""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            rmtree(self.export_dir)
        super().tearDown()

    def test_01_basic(self):
        """Import tar file."""
        archive_2 = f"{self.repo}::2"
        self.api.export_tar(self.archive, self.tar_file)
        self.assertRaises(Archive.DoesNotExist, self.api.info, archive_2)
        self.api.import_tar(archive_2, self.tar_file)
        output = self.api.info(archive_2, json=True)
        name = output["archives"][0]["name"]
        self.assertEqual(name, "2", "Archive not imported.")

    def test_02_stdin(self):
        """Import tar file from stdin."""
        archive_2 = f"{self.repo}::2"
        self.api.export_tar(self.archive, self.tar_file)
        self.assertRaises(Archive.DoesNotExist, self.api.info, archive_2)
        with open(self.tar_file, "rb") as fp:
            tar_data = fp.read()
            temp_stdin = TextIOWrapper(BytesIO(tar_data))
            sys.stdin = temp_stdin
        try:
            self.api.import_tar(archive_2, "-")
        finally:
            temp_stdin.close()
            sys.stdin = sys.__stdin__
        output = self.api.info(archive_2, json=True)
        name = output["archives"][0]["name"]
        self.assertEqual(name, "2", "Archive not imported.")


class ImportTarAsyncTests(BorgapiAsyncTests):
    """Import Tar command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async export tar tests."""
        await super().asyncSetUp()
        await self._create_default()

        self.export_dir = join(self.temp, "export")
        self._make_clean(self.export_dir)
        self.tar_file = join(self.export_dir, "export.tar")

    def tearDown(self):
        """Remove async data created for async export tar tests."""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            rmtree(self.export_dir)
        super().tearDown()

    async def test_01_basic(self):
        """Import async tar file."""
        archive_2 = f"{self.repo}::2"
        await self.api.export_tar(self.archive, self.tar_file)
        with self.assertRaises(Archive.DoesNotExist):
            await self.api.info(archive_2)
        await self.api.import_tar(archive_2, self.tar_file)
        output = await self.api.info(archive_2, json=True)
        name = output["archives"][0]["name"]
        self.assertEqual(name, "2", "Archive not imported.")

    async def test_02_stdin(self):
        """Import async tar file from stdin."""
        archive_2 = f"{self.repo}::2"
        await self.api.export_tar(self.archive, self.tar_file)
        with self.assertRaises(Archive.DoesNotExist):
            await self.api.info(archive_2)
        with open(self.tar_file, "rb") as fp:
            tar_data = fp.read()
            temp_stdin = TextIOWrapper(BytesIO(tar_data))
            sys.stdin = temp_stdin
        try:
            await self.api.import_tar(archive_2, "-")
        finally:
            temp_stdin.close()
            sys.stdin = sys.__stdin__
        output = await self.api.info(archive_2, json=True)
        name = output["archives"][0]["name"]
        self.assertEqual(name, "2", "Archive not imported.")
