"""Test list command"""
from .test_borgapi import BorgapiTests


class ListTests(BorgapiTests):
    """List command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

    def test_basic(self):
        """List repo archvies and archive files"""
        output = self.api.list(self.repo, json=True)
        num_archvies = len(output["archives"])
        self.assertEqual(num_archvies, 1, "Unexpected number of archives returned")

        output = self.api.list(self.archive, json_lines=True)
        num_files = len(output)
        self.assertEqual(num_files, 3, "Unexpected number of files returned")

    def test_repo_basic(self):
        """List repo"""
        output = self.api.list(self.repo)
        self._display("list repo", output)
        self.assertType(output, str)

    def test_repo_short(self):
        """List repo short"""
        output = self.api.list(self.repo, short=True)
        self._display("list repo short", output)
        self.assertType(output, str)

    def test_repo_json(self):
        """List repo json"""
        output = self.api.list(self.repo, json=True)
        self._display("list repo json", output)
        self.assertAnyType(output, list, dict)
        output = self.api.list(self.repo, log_json=True)
        self._display("list repo log json", output)
        self.assertAnyType(output, str)

    def test_archive_basic(self):
        """List archive"""
        output = self.api.list(self.archive)
        self._display("list archive", output)
        self.assertType(output, str)

    def test_archive_short(self):
        """List archive short"""
        output = self.api.list(self.archive, short=True)
        self._display("list archive short", output)
        self.assertType(output, str)

    def test_archive_json(self):
        """List archive json"""
        output = self.api.list(self.archive, json_lines=True)
        self._display("list archive json", output)
        self.assertAnyType(output, list, dict)
