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

    def tearDown(self):
        """Tear down export / import tests"""
        super().tearDown()
        rmtree(self.export_dir)

    def test_key_change_passphrase(self):
        """Change key passphrase"""
        api = self._init_and_create(self.repo, "1", self.data)

        repo_config_file = join(self.repo, "config")
        repo_config = self.read_config(filename=repo_config_file)

        original_value = repo_config["repository"]["key"]

        api.set_environ(dictionary={"BORG_NEW_PASSPHRASE": "newpass"})
        api.key_change_passphrase(self.repo)
        api.unset_environ("BORG_NEW_PASSPHRASE")

        repo_config = self.read_config(filename=repo_config_file)
        key_change_value = repo_config["repository"]["key"]

        self.assertNotEqual(
            key_change_value,
            original_value,
            "Changed key matches original",
        )

    def test_key_export(self):
        """Export repo excryption key"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.key_export(self.repo, self.key_file)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_key_export_paper(self):
        """Export repo excryption key"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.key_export(self.repo, self.key_file, paper=True)
        self.assertFileExists(
            self.key_file,
            "Repo key not exported to expected location",
        )

    def test_key_import(self):
        """Import original key to repository"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.key_export(self.repo, self.key_file)

        repo_config_file = join(self.repo, "config")
        repo_config = self.read_config(filename=repo_config_file)
        original_value = repo_config["repository"]["key"]

        api.key_import(self.repo, self.key_file)

        repo_config = self.read_config(filename=repo_config_file)
        restored_value = repo_config["repository"]["key"]

        self.assertEqual(
            restored_value,
            original_value,
            "Restored key does not match original",
        )
