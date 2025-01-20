"""Test key commands."""

from os.path import join
from shutil import rmtree

from . import BorgapiAsyncTests, BorgapiTests


class KeyTests(BorgapiTests):
    """Key command tests."""

    @classmethod
    def setUpClass(cls):
        """Prepare class data for key tests."""
        super().setUpClass()
        cls.export_dir = join(cls.temp, "export")
        cls.key_file = join(cls.export_dir, "key.txt")

    def setUp(self):
        """Prepare data for key tests."""
        super().setUp()
        self._make_clean(self.export_dir)
        self._create_default()

    def tearDown(self):
        """Remove data created for key tests."""
        rmtree(self.export_dir)
        super().tearDown()

    def test_01_change_passphrase(self):
        """Change key passphrase."""
        repo_config_file = join(self.repo, "config")
        repo_config = self._read_config(filename=repo_config_file)

        original_value = repo_config["repository"]["key"]

        self.api.set_environ(dictionary={"BORG_NEW_PASSPHRASE": "newpass"})
        self.api.key_change_passphrase(self.repo)
        self.api.unset_environ("BORG_NEW_PASSPHRASE")

        repo_config = self._read_config(filename=repo_config_file)
        key_change_value = repo_config["repository"]["key"]

        self.assertNotEqual(
            key_change_value,
            original_value,
            "Changed key matches original",
        )

    def test_02_export(self):
        """Export repo excryption key."""
        self.api.key_export(self.repo, self.key_file)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_03_export_paper(self):
        """Export repo excryption key."""
        self.api.key_export(self.repo, self.key_file, paper=True)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_04_import(self):
        """Import original key to repository."""
        self.api.key_export(self.repo, self.key_file)

        repo_config_file = join(self.repo, "config")
        repo_config = self._read_config(filename=repo_config_file)
        original_value = repo_config["repository"]["key"]

        self.api.key_import(self.repo, self.key_file)

        repo_config = self._read_config(filename=repo_config_file)
        restored_value = repo_config["repository"]["key"]

        self.assertEqual(
            restored_value,
            original_value,
            "Restored key does not match original",
        )


class KeyAsyncTests(BorgapiAsyncTests):
    """Key command tests."""

    @classmethod
    def setUpClass(cls):
        """Prepare class data for async key tests."""
        super().setUpClass()
        cls.export_dir = join(cls.temp, "export")
        cls.key_file = join(cls.export_dir, "key.txt")

    async def asyncSetUp(self):
        """Prepare async data for async key tests."""
        await super().asyncSetUp()
        self._make_clean(self.export_dir)
        await self._create_default()

    def tearDown(self):
        """Remove data created for async key tests."""
        rmtree(self.export_dir)
        super().tearDown()

    async def test_01_change_passphrase(self):
        """Change key passphrase."""
        repo_config_file = join(self.repo, "config")
        repo_config = self._read_config(filename=repo_config_file)

        original_value = repo_config["repository"]["key"]

        await self.api.set_environ(dictionary={"BORG_NEW_PASSPHRASE": "newpass"})
        await self.api.key_change_passphrase(self.repo)
        await self.api.unset_environ("BORG_NEW_PASSPHRASE")

        repo_config = self._read_config(filename=repo_config_file)
        key_change_value = repo_config["repository"]["key"]

        self.assertNotEqual(
            key_change_value,
            original_value,
            "Changed key matches original",
        )

    async def test_02_export(self):
        """Export repo excryption key."""
        await self.api.key_export(self.repo, self.key_file)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    async def test_03_export_paper(self):
        """Export repo excryption key."""
        await self.api.key_export(self.repo, self.key_file, paper=True)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    async def test_04_import(self):
        """Import original key to repository."""
        await self.api.key_export(self.repo, self.key_file)

        repo_config_file = join(self.repo, "config")
        repo_config = self._read_config(filename=repo_config_file)
        original_value = repo_config["repository"]["key"]

        await self.api.key_import(self.repo, self.key_file)

        repo_config = self._read_config(filename=repo_config_file)
        restored_value = repo_config["repository"]["key"]

        self.assertEqual(
            restored_value,
            original_value,
            "Restored key does not match original",
        )
