"""Test rename command"""
from borg.archive import Archive

from .test_borgapi import BorgapiTests


class RenameTests(BorgapiTests):
    """Rename command tests"""

    def test_rename(self):
        """Rename a archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        out, _ = api.list(self.repo, json=True)
        original_name = out["archives"][0]["name"]
        api.rename(f"{self.repo}::1", "2")
        out, _ = api.list(self.repo, json=True)
        new_name = out["archives"][0]["name"]
        self.assertNotEqual(new_name, original_name, "Name change did not occur")
        self.assertEqual(new_name, "2", "Name did not change to expected output")

    def test_rename_no_exist(self):
        """Rename nonexistant archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        self.assertRaises(
            Archive.DoesNotExist,
            api.rename,
            f"{self.repo}::2",
            "3",
            msg="Renamed archive that does not exist",
        )
