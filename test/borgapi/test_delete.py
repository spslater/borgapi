"""Test delete command"""
from borg.archive import Archive
from borg.repository import Repository

from borgapi import BorgAPI

from .test_borgapi import BorgapiTests


class DeleteTests(BorgapiTests):
    """Delete command tests"""

    def test_delete_repository(self):
        """Delete repository"""
        api = self._init_and_create(self.repo, "1", self.data)
        api.delete(self.repo)
        self.assertRaises(
            Repository.DoesNotExist,
            api.list,
            self.repo,
            msg="Deleted repository still exists",
        )

    # pylint: disable=invalid-name
    def test_delete_repository_not_exist(self):
        """Delete repository that doesn't exist"""
        api = BorgAPI()
        self.assertRaises(
            Repository.InvalidRepository,
            api.delete,
            self.repo,
            msg="Deleted nonexistant repository",
        )

    def test_delete_archive(self):
        """Delete archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        api.delete(f"{self.repo}::1")
        self.assertRaises(
            Archive.DoesNotExist,
            api.list,
            f"{self.repo}::1",
            msg="Deleted archive still exists",
        )

    def test_delete_archive_not_exist(self):
        """Delete archvie that doesn't exist"""
        api = self._init_and_create(self.repo, "1", self.data)

        with self.assertLogs("borg", "WARNING") as logger:
            api.delete(f"{self.repo}::2")

        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?2.*not found",
            "Warning not logged for bad archive name",
        )
