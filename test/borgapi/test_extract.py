"""Test extract command"""
from os import remove

from .test_borgapi import BorgapiTests


class ExtractTests(BorgapiTests):
    """Extract command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

    def test_basic(self):
        """Extract file"""
        remove(self.file_1)
        self.assertFileNotExists(self.file_1)

        self.api.extract(self.archive, self.file_1)
        self.assertFileExists(self.file_1)

    def test_not_exist(self):
        """Extract path that does not exist"""
        with self.assertLogs("borg", "WARNING") as logger:
            self.api.extract(self.archive, self.file_3)
        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?file_3.*never",
            "Warning not logged for bad path",
        )

    def test_stdout(self):
        """Capture Extracted File"""
        output = self.api.extract(self.archive, self.file_1, stdout=True)
        self.assertEqual(
            output,
            bytes(self.file_1_text, "utf-8"),
            "Extracted file text does not match",
        )

    def test_output_string(self):
        """list to log"""
        output = self.api.extract(self.archive, list=True, dry_run=True)
        self._display("extract 1", output)
        self.assertType(output, str)

    def test_output_json(self):
        """list to json"""
        output = self.api.extract(self.archive, log_json=True, list=True, dry_run=True)
        self._display("extract 2", output)
        self.assertAnyType(output, str)
