"""Test config command"""
from .test_borgapi import BorgapiTests


class ConfigTests(BorgapiTests):
    """Config command tests"""

    def setUp(self):
        super().setUp()
        self._create_default()

    def test_list(self):
        """List config values for repo"""
        output = self.api.config(self.repo, list=True)
        self._display("config list", output)
        self.assertType(output, str)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "0", "Unexpected config value")

    def test_value(self):
        """List config value"""
        output = self.api.config(self.repo, "additional_free_space")
        self._display("config value", output)
        self.assertType(output, list)
        self.assertEqual(output[0], "0", "Unexpected config value")

    def test_change(self):
        """Change config values in repo"""
        self.api.config(self.repo, ("append_only", "1"))
        output = self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "1", "Unexpected config value")

    def test_delete(self):
        """Delete config value from repo"""
        self.api.config(self.repo, "additional_free_space", delete=True)
        output = self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        additional_free_space = repo_config["repository"]["additional_free_space"]
        self.assertEqual(additional_free_space, "False", "Unexpected config value")
