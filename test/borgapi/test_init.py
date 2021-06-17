"""Test init command"""
from os import urandom
from os.path import join

from borg.repository import Repository

from .test_borgapi import BorgapiTests


class InitTests(BorgapiTests):
    """Init command tests"""

    def setUp(self):
        super().setUp()
        self._make_clean(self.repo)

    def test_basic(self):
        """Initalize new repository"""
        self.api.init(self.repo)
        self.assertFileExists(join(self.repo, "README"))

    def test_already_exists(self):
        """Initalize a repo in a directory where one already exists"""
        self.api.init(self.repo)
        self.assertRaises(
            Repository.AlreadyExists,
            self.api.init,
            self.repo,
            msg="Duplicate repositroy overwrites old repo",
        )

    def test_path_exists(self):
        """Initalize a repo in a directory where other data exists"""
        self.api.init(self.repo)
        self.assertRaises(
            Repository.PathAlreadyExists,
            self.api.init,
            self.data,
            msg="Repositroy overwrites directory with other data",
        )

    def test_make_parent(self):
        """Init a repo where parents don't exist with different flags"""
        deep_repo = join(self.repo, "make/parents")

        self.assertRaises(
            Repository.ParentPathDoesNotExist,
            self.api.init,
            deep_repo,
            msg="Repository made with missing directories",
        )
        self.api.init(deep_repo, make_parent_dirs=True)
        output = self.api.list(deep_repo, json=True)
        self.assertKeyExists("repository", output, "Repository not initalzied")

    def test_storage_quota(self):
        """Limit the size of the repo"""
        self.api.init(self.repo, storage_quota="10M")
        with open(self.file_3, "wb") as fp:
            fp.write(urandom(10 * 1024 * 1024))
        self.assertRaises(
            Repository.StorageQuotaExceeded,
            self.api.create,
            self.archive,
            self.data,
            msg="Stored more than quota allowed",
        )

    def test_append_only(self):
        """Repo in append only mode"""
        self.api.init(self.repo, append_only=True)
        output = self.api.config(self.repo, list=True)
        config = self._read_config(output)
        self.assertEqual(
            config["repository"]["append_only"],
            "1",
            "Repo not in append_only mode",
        )
