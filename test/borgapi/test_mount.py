"""Test mount and unmount commands"""
from os import getenv
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class MountTests(BorgapiTests):
    """Mount and Unmount command tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mountpoint = join(cls.temp, "mount")
        cls.repo_file = join(cls.mountpoint, "1", cls.file_1)
        cls.archive_file = join(cls.mountpoint, cls.file_1)

    def setUp(self):
        if getenv("BORGAPI_TEST_MOUNT_SKIP"):
            self.skipTest("llfuse not setup")
        super().setUp()
        self._create_default()
        self._make_clean(self.mountpoint)

    def tearDown(self):
        rmtree(self.mountpoint)
        super().tearDown()

    def test_repository(self):
        """Mount and unmount a repository"""
        self.api.mount(self.repo, self.mountpoint)
        self.assertFileExists(self.repo_file)
        self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.repo_file)

    def test_archive(self):
        """Mount and unmount a archive"""
        self.api.mount(self.archive, self.mountpoint)
        self.assertFileExists(self.archive_file)
        self.api.umount(self.mountpoint)
        self.assertFileNotExists(self.archive_file)
