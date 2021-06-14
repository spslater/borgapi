"""Test info command"""
from .test_borgapi import BorgapiTests


class BorgapiOther(BorgapiTests):
    """Info command tests"""

    def test_info_repository(self):
        """Repository info"""
        api = self._init_and_create(self.repo, "1", self.data)

        output = api.info(self.repo, json=True)
        self.assertKeyExists("cache", output["info"])
        self.assertKeyNotExists("archives", output["info"])

    def test_info_archive(self):
        """Archive info"""
        api = self._init_and_create(self.repo, "1", self.data)

        output = api.info(f"{self.repo}::1", json=True)
        self.assertKeyExists("cache", output["info"])
        self.assertKeyExists("archives", output["info"])
