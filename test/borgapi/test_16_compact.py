"""Test deff command"""
from .test_01_borgapi import BorgapiTests


class CompactTests(BorgapiTests):
    """Compact command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        self.api.delete(self.archive)

    def test_01_output(self):
        """Compact string"""
        output = self.api.compact(self.repo)
        self._display("compact sting", output)
        self.assertNone(output)

    def test_02_output_verbose(self):
        """Compact string"""
        output = self.api.compact(self.repo, verbose=True)
        self._display("compact sting verbose", output)
        self.assertType(output, str)

    def test_03_output_json(self):
        """Compact json"""
        output = self.api.compact(self.repo, verbose=True, log_json=True)
        self._display("compact log json", output)
        self.assertAnyType(output, dict)

