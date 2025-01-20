"""Test init command."""

from os import urandom
from os.path import join

from borg.repository import Repository

from . import BorgapiAsyncTests, BorgapiTests


class InitTests(BorgapiTests):
    """Init command tests."""

    def setUp(self):
        """Prepare data for init tests."""
        super().setUp()
        self._make_clean(self.repo)

    def test_01_basic(self):
        """Initalize new repository."""
        self.api.init(self.repo)
        self.assertFileExists(join(self.repo, "README"))

    def test_02_already_exists(self):
        """Initalize a repo in a directory where one already exists."""
        self.api.init(self.repo)
        self.assertRaises(
            Repository.AlreadyExists,
            self.api.init,
            self.repo,
            msg="Duplicate repositroy overwrites old repo",
        )

    def test_03_path_exists(self):
        """Initalize a repo in a directory where other data exists."""
        self.api.init(self.repo)
        self.assertRaises(
            Repository.PathAlreadyExists,
            self.api.init,
            self.data,
            msg="Repositroy overwrites directory with other data",
        )

    def test_04_make_parent(self):
        """Init a repo where parents don't exist with different flags."""
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

    def test_05_storage_quota(self):
        """Limit the size of the repo."""
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

    def test_06_append_only(self):
        """Repo in append only mode."""
        self.api.init(self.repo, append_only=True)
        output = self.api.config(self.repo, list=True)
        config = self._read_config(output)
        self.assertEqual(
            config["repository"]["append_only"],
            "1",
            "Repo not in append_only mode",
        )


class InitAsyncTests(BorgapiAsyncTests):
    """Init command tests."""

    def setUp(self):
        """Prepare data for async init tests."""
        super().setUp()
        # self._make_clean(self.repo)

    async def asyncSetUp(self):
        """Prepare async data for async init tests."""
        await super().asyncSetUp()
        self._make_clean(self.repo)

    async def test_01_basic(self):
        """Initalize new repository."""
        await self.api.init(self.repo)
        self.assertFileExists(join(self.repo, "README"))

    async def test_02_already_exists(self):
        """Initalize a repo in a directory where one already exists."""
        await self.api.init(self.repo)
        with self.assertRaises(
            Repository.AlreadyExists,
            msg="Duplicate repositroy overwrites old repo",
        ):
            await self.api.init(self.repo)

    async def test_03_path_exists(self):
        """Initalize a repo in a directory where other data exists."""
        await self.api.init(self.repo)
        with self.assertRaises(
            Repository.PathAlreadyExists,
            msg="Repositroy overwrites directory with other data",
        ):
            await self.api.init(self.data)

    async def test_04_make_parent(self):
        """Init a repo where parents don't exist with different flags."""
        deep_repo = join(self.repo, "make/parents")

        with self.assertRaises(
            Repository.ParentPathDoesNotExist,
            msg="Repository made with missing directories",
        ):
            await self.api.init(deep_repo)
        await self.api.init(deep_repo, make_parent_dirs=True)
        output = await self.api.list(deep_repo, json=True)
        self.assertKeyExists("repository", output, "Repository not initalzied")

    async def test_05_storage_quota(self):
        """Limit the size of the repo."""
        await self.api.init(self.repo, storage_quota="10M")
        with open(self.file_3, "wb") as fp:
            fp.write(urandom(10 * 1024 * 1024))
        with self.assertRaises(
            Repository.StorageQuotaExceeded,
            msg="Stored more than quota allowed",
        ):
            await self.api.create(self.archive, self.data)

    async def test_06_append_only(self):
        """Repo in append only mode."""
        await self.api.init(self.repo, append_only=True)
        output = await self.api.config(self.repo, list=True)
        config = self._read_config(output)
        self.assertEqual(
            config["repository"]["append_only"],
            "1",
            "Repo not in append_only mode",
        )
