"""Test deff command"""
from .test_borgapi import BorgapiTests


class DiffTests(BorgapiTests):
    """Diff command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

    def test_add_file(self):
        """Diff new file"""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", json_lines=True)
        self.assertType(output, dict)
        modify_path = output["path"]
        modify_type = output["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_3, "Unexpected new filename")
        self.assertEqual(modify_type, "added", "New file not listed as added")

    def test_modify_file(self):
        """Diff modified file"""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", json_lines=True, sort=True)
        self.assertType(output, list)
        modify_path = output[0]["path"]
        modify_type = output[0]["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_2, "Unexpected file changed")
        self.assertEqual(modify_type, "modified", "Unexpected change type")

    def test_output(self):
        """Diff string"""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2")
        self._display("diff sting", output)
        self.assertType(output, str)

    def test_output_json(self):
        """Diff json"""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", log_json=True)
        self._display("diff log json", output)
        self.assertAnyType(output, str)
