"""Test list command"""
from .test_borgapi import BorgapiTests


class ListTests(BorgapiTests):
    """List command tests"""

    def test_list(self):
        """List repo archvies and archive files"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.list(self.repo, json=True)
        num_archvies = len(out["archives"])
        self.assertEqual(num_archvies, 1, "Unexpected number of archives returned")

        out, _ = api.list(f"{self.repo}::1", json_lines=True)
        num_files = len(out)
        self.assertEqual(num_files, 3, "Unexpected number of files returned")
