"""Test extract command"""
from os import remove

from .test_borgapi import BorgapiTests


class ExtractTests(BorgapiTests):
    """Extract command tests"""

    def test_extract(self):
        """Extract file"""
        api = self._init_and_create(self.repo, "1", self.data)

        remove(self.file_1)
        self.assertFileNotExists(self.file_1)

        api.extract(f"{self.repo}::1", self.file_1)
        self.assertFileExists(self.file_1)

    def test_extract_not_exist(self):
        """Extract path that does not exist"""
        api = self._init_and_create(self.repo, "1", self.data)

        with self.assertLogs("borg", "WARNING") as logger:
            api.extract(f"{self.repo}::1", self.file_3)
        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?file_3.*never",
            "Warning not logged for bad path",
        )

    def test_extract_stdout(self):
        """Capture Extracted File"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.extract(f"{self.repo}::1", self.file_1, stdout=True)
        self.assertEqual(
            out,
            bytes(self.file_1_text, "utf-8"),
            "Extracted file text does not match",
        )
