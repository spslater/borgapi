"""Test create command"""
import sys
from io import BytesIO, TextIOWrapper

from borg.archive import Archive

from .test_borgapi import BorgapiTests


class CreateTests(BorgapiTests):
    """Create command tests"""

    def test_create(self):
        """Create new archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        output = api.list(self.repo, json=True)
        num_archives = len(output["list"]["archives"])
        self.assertEqual(num_archives, 1, "Archive not saved")
        archive_name = output["list"]["archives"][0]["name"]
        self.assertEqual(archive_name, "1", "Archive name does not match set name")

    def test_create_second(self):
        """Create second archive after data modification"""
        api = self._init_and_create(self.repo, "1", self.data)

        with open(self.file_3, "w+") as fp:
            fp.write("New Data")
        api.create(f"{self.repo}::2", self.data)

        output = api.list(self.repo, json=True)
        num_archives = len(output["list"]["archives"])
        self.assertEqual(num_archives, 2, "Multiple archives not saved")
        archive_1_name = output["list"]["archives"][0]["name"]
        self.assertEqual(archive_1_name, "1", "Archive name does not match set name")
        archive_2_name = output["list"]["archives"][1]["name"]
        self.assertEqual(archive_2_name, "2", "Archive name does not match set name")

    def test_create_already_exists(self):
        """Create an archive with an existing name"""
        api = self._init_and_create(self.repo, "1", self.data)

        self.assertRaises(
            Archive.AlreadyExists,
            api.create,
            f"{self.repo}::1",
            self.data,
        )

    def test_create_stdin(self):
        """Read input from stdin and save to archvie"""
        api = self._init_and_create(self.repo, "1", self.data)

        temp_stdin = TextIOWrapper(BytesIO(bytes(self.file_3_text, "utf-8")))
        sys.stdin = temp_stdin

        archive = f"{self.repo}::2"
        name = "file_3_stdin.txt"
        mode = "0777"  # "-rwxrwxrwx"

        try:
            api.create(
                archive,
                "-",
                stdin_name=name,
                stdin_mode=mode,
            )
        finally:
            temp_stdin.close()
            sys.stdin = sys.__stdin__

        output = api.list(archive, json_lines=True)
        self.assertEqual(output["list"]["path"], name, "Unexpected file name")
        self.assertEqual(output["list"]["mode"], "-rwxrwxrwx", "Unexpected file mode")
