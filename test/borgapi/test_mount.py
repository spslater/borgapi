"""Test mount and unmount commands"""
import unittest
from os import getenv
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class MountTests(BorgapiTests):
    """Mount and Unmount command tests"""

    @unittest.skipIf(
        getenv("BORGAPI_TEST_MOUNT_SKIP"),
        "llfuse not setup, skipping",
    )
    def test_mount_umount_archive(self):
        """Mount and unmount a archive"""
        api = self._init_and_create(self.repo, "1", self.data)

        mount = join(self.temp, "mount")
        self._make_clean(mount)
        api.mount(self.repo, mount)

        file_1_mount = join(mount, "1", self.file_1)
        self.assertFileExists(file_1_mount)

        rmtree(mount)

    @unittest.skipIf(
        getenv("BORGAPI_TEST_MOUNT_SKIP"),
        "llfuse not setup, skipping",
    )
    def test_mount_umount_repository(self):
        """Mount and unmount a repository"""
        api = self._init_and_create(self.repo, "1", self.data)

        mount = join(self.temp, "mount")
        self._make_clean(mount)
        api.mount(f"{self.repo}::1", mount)

        file_1_mount = join(mount, self.file_1)
        self.assertFileExists(file_1_mount)

        rmtree(mount)
