"""Test init command"""
from os import urandom
from os.path import join

from borg.repository import Repository

from borgapi import BorgAPI

from .test_borgapi import BorgapiTests


class InitTests(BorgapiTests):
    """Init command tests"""

    def test_init(self):
        """Initalize new repository"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertFileExists(join(self.repo, "README"))

    def test_init_already_exists(self):
        """Initalize a repo in a directory where one already exists"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertRaises(
            Repository.AlreadyExists,
            api.init,
            self.repo,
            msg="Duplicate repositroy overwrites old repo",
        )

    def test_init_path_exists(self):
        """Initalize a repo in a directory where other data exists"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertRaises(
            Repository.PathAlreadyExists,
            api.init,
            self.data,
            msg="Repositroy overwrites directory with other data",
        )

    def test_init_make_parent(self):
        """Init a repo where parents don't exist with different flags"""
        api = BorgAPI()
        deep_repo = join(self.repo, "make/parents")

        self.assertRaises(
            Repository.ParentPathDoesNotExist,
            api.init,
            deep_repo,
            msg="Repository made with missing directories",
        )
        api.init(deep_repo, make_parent_dirs=True)
        output = api.list(deep_repo, json=True)
        self.assertKeyExists("repository", output["list"], "Repository not initalzied")

    def test_init_storage_quota(self):
        """Limit the size of the repo"""
        api = BorgAPI()
        api.init(self.repo, storage_quota="10M")
        with open(self.file_3, "wb") as fp:
            fp.write(urandom(10 * 1024 * 1024))
        self.assertRaises(
            Repository.StorageQuotaExceeded,
            api.create,
            f"{self.repo}::1",
            self.data,
            msg="Stored more than quota allowed",
        )

    def test_init_append_only(self):
        """Repo in append only mode"""
        api = BorgAPI()
        api.init(self.repo, append_only=True)
        output = api.config(self.repo, list=True)
        config = self.read_config(output["list"])
        self.assertEqual(
            config["repository"]["append_only"],
            "1",
            "Repo not in append_only mode",
        )
