"""Test rename command."""

from borg.archive import Archive

from . import BorgapiAsyncTests, BorgapiTests


class RenameTests(BorgapiTests):
    """Rename command tests."""

    def setUp(self):
        """Prepare data for rename tests."""
        super().setUp()
        self._create_default()

    def test_01_basic(self):
        """Rename a archive."""
        output = self.api.list(self.repo, json=True)
        original_name = output["archives"][0]["name"]
        self.api.rename(self.archive, "2")
        output = self.api.list(self.repo, json=True)
        new_name = output["archives"][0]["name"]
        self.assertNotEqual(new_name, original_name, "Name change did not occur")
        self.assertEqual(new_name, "2", "Name did not change to expected output")

    def test_02_no_exist(self):
        """Rename nonexistant archive."""
        self.assertRaises(
            Archive.DoesNotExist,
            self.api.rename,
            f"{self.repo}::2",
            "3",
            msg="Renamed archive that does not exist",
        )


class RenameAsyncTests(BorgapiAsyncTests):
    """Rename command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async rename tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_basic(self):
        """Rename a archive."""
        output = await self.api.list(self.repo, json=True)
        original_name = output["archives"][0]["name"]
        await self.api.rename(self.archive, "2")
        output = await self.api.list(self.repo, json=True)
        new_name = output["archives"][0]["name"]
        self.assertNotEqual(new_name, original_name, "Name change did not occur")
        self.assertEqual(new_name, "2", "Name did not change to expected output")

    async def test_02_no_exist(self):
        """Rename nonexistant archive."""
        with self.assertRaises(
            Archive.DoesNotExist,
            msg="Renamed archive that does not exist",
        ):
            await self.api.rename(f"{self.repo}::2", "3")
