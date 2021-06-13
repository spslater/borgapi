"""Test info command"""
from .test_borgapi import BorgapiTests


class BorgapiOther(BorgapiTests):
    """Info command tests"""

    def test_info_repository(self):
        """Repository info"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.info(self.repo, json=True)
        self.assertKeyExists("cache", out)
        self.assertKeyNotExists("archives", out)

    def test_info_archive(self):
        """Archive info"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.info(f"{self.repo}::1", json=True)
        self.assertKeyExists("cache", out)
        self.assertKeyExists("archives", out)
