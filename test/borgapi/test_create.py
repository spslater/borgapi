"""Test create command"""
import sys
from io import BytesIO, TextIOWrapper

from borg.archive import Archive

from .test_borgapi import BorgapiTests


class CreateTests(BorgapiTests):
    """Create command tests"""

    def test_basic(self):
        """Create new archive"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 1, "Archive not saved")
        archive_name = output["archives"][0]["name"]
        self.assertEqual(archive_name, "1", "Archive name does not match set name")

    def test_second(self):
        """Create second archive after data modification"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w+") as fp:
            fp.write("New Data")
        self.api.create(f"{self.repo}::2", self.data)

        output = self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 2, "Multiple archives not saved")
        archive_1_name = output["archives"][0]["name"]
        self.assertEqual(archive_1_name, "1", "Archive name does not match set name")
        archive_2_name = output["archives"][1]["name"]
        self.assertEqual(archive_2_name, "2", "Archive name does not match set name")

    def test_already_exists(self):
        """Create an archive with an existing name"""
        self.api.create(self.archive, self.data)
        self.assertRaises(
            Archive.AlreadyExists,
            self.api.create,
            self.archive,
            self.data,
        )

    def test_stdin(self):
        """Read input from stdin and save to archvie"""
        temp_stdin = TextIOWrapper(BytesIO(bytes(self.file_3_text, "utf-8")))
        sys.stdin = temp_stdin
        name = "file_3_stdin.txt"
        mode = "0777"  # "-rwxrwxrwx"

        try:
            self.api.create(
                self.archive,
                "-",
                stdin_name=name,
                stdin_mode=mode,
            )
        finally:
            temp_stdin.close()
            sys.stdin = sys.__stdin__

        output = self.api.list(self.archive, json_lines=True)
        self.assertEqual(output["path"], name, "Unexpected file name")
        self.assertEqual(output["mode"], "-rwxrwxrwx", "Unexpected file mode")

    def test_output_string(self):
        """Create string info"""
        output = self.api.create(self.archive, self.data, stats=True, list=True)
        self._display("create string info", output, False)
        self.assertType(output["stats"], str)
        self.assertType(output["list"], str)

    def test_output_json(self):
        """Create json info"""
        output = self.api.create(
            self.archive,
            self.data,
            json=True,
            log_json=True,
            list=True,
        )
        self._display("create string info", output, False)
        self.assertType(output["stats"], dict)
        self.assertAnyType(output["list"], list, dict)

    def test_output_mixed_1(self):
        """Create mixed output (stats json, list string)"""
        output = self.api.create(self.archive, self.data, json=True, list=True)
        self._display("create mixed output (stats json, list string)", output, False)
        self.assertType(output["stats"], dict)
        self.assertType(output["list"], str)

    def test_output_mixed_2(self):
        """Create mixed output (stats string, list json)"""
        output = self.api.create(
            self.archive,
            self.data,
            stats=True,
            log_json=True,
            list=True,
        )
        self._display("create mixed output (stats string, list json)", output, False)
        self.assertType(output["stats"], str)
        self.assertAnyType(output["list"], list, dict)

    def test_list_string(self):
        """Create list string"""
        output = self.api.create(self.archive, self.data, list=True)
        self._display("create list string", output)
        self.assertType(output, str)

    def test_stats_json(self):
        """Create stats json"""
        output = self.api.create(self.archive, self.data, json=True)
        self._display("create stats json", output)
        self.assertType(output, dict)

    def test_list_json(self):
        """Create list json"""
        output = self.api.create(
            self.archive,
            self.data,
            log_json=True,
            list=True,
        )
        self._display("create list json", output)
        self.assertAnyType(output, list, dict)

    def test_stats_string(self):
        """Create stats string"""
        output = self.api.create(self.archive, self.data, stats=True)
        self._display("create stats string", output)
        self.assertType(output, str)
