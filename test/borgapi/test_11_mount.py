"""Test mount and unmount commands."""

from os import getenv
from os.path import join
from shutil import rmtree
from time import sleep

from . import BorgapiAsyncTests, BorgapiTests


class MountTests(BorgapiTests):
    """Mount and Unmount command tests."""

    @classmethod
    def setUpClass(cls):
        """Prepare class data for mount tests."""
        super().setUpClass()
        cls.mountpoint = join(cls.temp, "mount")
        cls.repo_file = join(cls.mountpoint, "1", cls.file_1)
        cls.archive_file = join(cls.mountpoint, cls.file_1)

    def setUp(self):
        """Prepare data for mount tests."""
        if getenv("BORGAPI_TEST_MOUNT_SKIP"):
            self.skipTest("llfuse not setup")
        super().setUp()
        self._create_default()
        self._make_clean(self.mountpoint)

    def tearDown(self):
        """Remove data created for mount tests."""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            rmtree(self.mountpoint)
        super().tearDown()

    def test_01_repository(self):
        """Mount and unmount a repository."""
        output = self.api.mount(self.repo, self.mountpoint)
        sleep(5)
        self.assertTrue(output["pid"] != 0)
        self.assertFileExists(self.repo_file)
        self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.repo_file)
        sleep(3)

    def test_02_archive(self):
        """Mount and unmount a archive."""
        output = self.api.mount(self.archive, self.mountpoint)
        sleep(5)
        self.assertTrue(output["pid"] != 0)
        self.assertFileExists(self.archive_file)
        self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.archive_file)
        sleep(3)


class MountAsyncTests(BorgapiAsyncTests):
    """Mount and Unmount command tests."""

    @classmethod
    def setUpClass(cls):
        """Prepare class data for mount tests."""
        super().setUpClass()
        cls.mountpoint = join(cls.temp, "mount")
        cls.repo_file = join(cls.mountpoint, "1", cls.file_1)
        cls.archive_file = join(cls.mountpoint, cls.file_1)

    async def asyncSetUp(self):
        """Prepare async data for mount tests."""
        if getenv("BORGAPI_TEST_MOUNT_SKIP"):
            self.skipTest("llfuse not setup")
        await super().asyncSetUp()
        await self._create_default()
        self._make_clean(self.mountpoint)

    def tearDown(self):
        """Remove data created for async mount tests."""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            rmtree(self.mountpoint)
        super().tearDown()

    async def test_01_repository(self):
        """Mount and unmount a repository."""
        output = await self.api.mount(self.repo, self.mountpoint)
        sleep(5)
        self.assertTrue(output["pid"] != 0)
        self.assertFileExists(self.repo_file)
        await self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.repo_file)
        sleep(3)

    async def test_02_archive(self):
        """Mount and unmount a archive."""
        output = await self.api.mount(self.archive, self.mountpoint)
        sleep(5)
        self.assertTrue(output["pid"] != 0)
        self.assertFileExists(self.archive_file)
        await self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.archive_file)
        sleep(3)
