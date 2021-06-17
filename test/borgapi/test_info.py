"""Test info command"""
from .test_borgapi import BorgapiTests


class InfoTests(BorgapiTests):
    """Info command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

    def test_repository(self):
        """Repository info"""
        output = self.api.info(self.repo, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyNotExists("archives", output)

    def test_archive(self):
        """Archive info"""
        output = self.api.info(self.archive, json=True)
        self.assertKeyExists("cache", output)
        self.assertKeyExists("archives", output)

    def test_repo_string(self):
        """Repo output string"""
        output = self.api.info(self.repo)
        self._display("info repo string", output)
        self.assertType(output, str)

    def test_repo_json(self):
        """Repo output json"""
        output = self.api.info(self.repo, json=True)
        self._display("info repo json", output)
        self.assertAnyType(output, list, dict)

        output = self.api.info(self.repo, log_json=True)
        self._display("info repo log json", output)
        self.assertType(output, str)

    def test_archive_string(self):
        """Archive output string"""
        output = self.api.info(self.archive)
        self._display("info archive string", output)
        self.assertType(output, str)

    def test_archive_json(self):
        """Archive output json"""
        output = self.api.info(self.archive, json=True)
        self._display("info archive json", output)
        self.assertAnyType(output, list, dict)
