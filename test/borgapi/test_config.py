"""Test config command"""
from .test_borgapi import BorgapiTests


class ConfigTests(BorgapiTests):
    """Config command tests"""

    def test_config_list(self):
        """List config values for repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.config(self.repo, list=True)
        repo_config = self.read_config(out)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "0", "Unexpected config value")

        out, _ = api.config(self.repo, "additional_free_space")
        self.assertEqual(out[0], "0", "Unexpected config value")

    def test_config_change(self):
        """Change config values in repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.config(self.repo, ("append_only", "1"))
        out, _ = api.config(self.repo, list=True)
        repo_config = self.read_config(out)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "1", "Unexpected config value")

    def test_config_delete(self):
        """Delete config value from repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.config(self.repo, "additional_free_space", delete=True)
        out, _ = api.config(self.repo, list=True)
        repo_config = self.read_config(out)
        additional_free_space = repo_config["repository"]["additional_free_space"]
        self.assertEqual(additional_free_space, "False", "Unexpected config value")