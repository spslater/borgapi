"""Test config command."""

from . import BorgapiAsyncTests, BorgapiTests


class ConfigTests(BorgapiTests):
    """Config command tests."""

    def setUp(self):
        """Prepare data for config tests."""
        super().setUp()
        self._create_default()

    def test_01_list(self):
        """List config values for repo."""
        output = self.api.config(self.repo, list=True)
        self._display("config list", output)
        self.assertType(output, str)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "0", "Unexpected config value")

    def test_02_value(self):
        """List config value."""
        output = self.api.config(self.repo, "additional_free_space")
        self._display("config value", output)
        self.assertType(output, str)
        self.assertEqual(output, "0", "Unexpected config value")

    def test_03_change(self):
        """Change config values in repo."""
        self.api.config(self.repo, ("append_only", "1"))
        output = self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "1", "Unexpected config value")

    def test_04_delete(self):
        """Delete config value from repo."""
        self.api.config(self.repo, "additional_free_space", delete=True)
        output = self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        additional_free_space = repo_config["repository"]["additional_free_space"]
        self.assertEqual(additional_free_space, "False", "Unexpected config value")


class ConfigAsyncTests(BorgapiAsyncTests):
    """Config command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async config tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_list(self):
        """List config values for repo."""
        output = await self.api.config(self.repo, list=True)
        self._display("config list", output)
        self.assertType(output, str)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "0", "Unexpected config value")

    async def test_02_value(self):
        """List config value."""
        output = await self.api.config(self.repo, "additional_free_space")
        self._display("config value", output)
        self.assertType(output, str)
        self.assertEqual(output, "0", "Unexpected config value")

    async def test_03_change(self):
        """Change config values in repo."""
        await self.api.config(self.repo, ("append_only", "1"))
        output = await self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "1", "Unexpected config value")

    async def test_04_delete(self):
        """Delete config value from repo."""
        await self.api.config(self.repo, "additional_free_space", delete=True)
        output = await self.api.config(self.repo, list=True)
        repo_config = self._read_config(output)
        additional_free_space = repo_config["repository"]["additional_free_space"]
        self.assertEqual(additional_free_space, "False", "Unexpected config value")
