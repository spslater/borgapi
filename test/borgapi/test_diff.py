"""Test deff command"""
from .test_borgapi import BorgapiTests


class DiffTests(BorgapiTests):
    """Diff command tests"""

    def test_diff_add_file(self):
        """Diff two archives"""
        api = self._init_and_create(self.repo, "1", self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::2", self.data)
        output = api.diff(f"{self.repo}::1", "2", json_lines=True)
        modify_path = output["diff"]["path"]
        modify_type = output["diff"]["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_3, "Unexpected new filename")
        self.assertEqual(modify_type, "added", "New file not listed as added")

    def test_diff_modify_file(self):
        """File diff of two archives"""
        api = self._init_and_create(self.repo, "1", self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::2", self.data)
        output = api.diff(f"{self.repo}::1", "2", json_lines=True, sort=True)
        modify_path = output["diff"][0]["path"]
        modify_type = output["diff"][0]["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_2, "Unexpected file changed")
        self.assertEqual(modify_type, "modified", "Unexpected change type")
