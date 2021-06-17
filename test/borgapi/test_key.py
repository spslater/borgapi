"""Test key commands"""
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class KeyTests(BorgapiTests):
    """Key command tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export_dir = join(cls.temp, "export")
        cls.key_file = join(cls.export_dir, "key.txt")

    def setUp(self):
        """Setup export / import tests"""
        super().setUp()
        self._make_clean(self.export_dir)
        self._create_default()

    def tearDown(self):
        """Tear down export / import tests"""
        rmtree(self.export_dir)
        super().tearDown()

    def test_change_passphrase(self):
        """Change key passphrase"""
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

    def test_export(self):
        """Export repo excryption key"""
        self.api.key_export(self.repo, self.key_file)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_export_paper(self):
        """Export repo excryption key"""
        self.api.key_export(self.repo, self.key_file, paper=True)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_import(self):
        """Import original key to repository"""
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
