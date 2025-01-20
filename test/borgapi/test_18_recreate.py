"""Test create command."""

from . import BorgapiAsyncTests, BorgapiTests


class RecreateTests(BorgapiTests):
    """Recreate command tests."""

    def test_01_basic(self):
        """Recreate archive."""
        self.api.create(self.archive, self.data, compression="lz4")
        self.api.recreate(self.archive, recompress="always", compression="zlib,9", target="2")
        output = self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 2, "Archive not recreated")

    def test_02_comment(self):
        """Change archive comment."""
        self.api.create(self.archive, self.data, comment="first")
        self.api.recreate(self.archive, comment="second")
        output = self.api.info(self.archive, json=True)
        comment = output["archives"][0]["comment"]
        self.assertEqual(comment, "second", "Archive comment not updated")

    def test_03_remove_file(self):
        """Change archive comment."""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w+") as fp:
            fp.write("New Data")
        archive_2 = f"{self.repo}::2"
        self.api.create(archive_2, self.data)
        self.api.recreate(self.repo, exclude=self.file_2)
        first = self.api.list(self.archive, json_lines=True)
        infirst = [v for v in first if v["path"] == self.file_2]
        self.assertEqual(len(first), 2, "Incorrect number of files in first archive.")
        self.assertEqual(len(infirst), 0, "Path removed from first archive.")
        second = self.api.list(archive_2, json_lines=True)
        insecond = [v for v in first if v["path"] == self.file_2]
        self.assertEqual(len(second), 3, "Incorrect number of files in second archive.")
        self.assertEqual(len(insecond), 0, "Path removed from second archive.")


class RecreateAsyncTests(BorgapiAsyncTests):
    """Create command tests."""

    async def test_01_basic(self):
        """Create new archive."""
        await self.api.create(self.archive, self.data, compression="lz4")
        await self.api.recreate(self.archive, recompress="always", compression="zlib,9", target="2")
        output = await self.api.list(self.repo, json=True)
        num_archives = len(output["archives"])
        self.assertEqual(num_archives, 2, "Archive not recreated")

    async def test_02_comment(self):
        """Change archive comment."""
        await self.api.create(self.archive, self.data, comment="first")
        await self.api.recreate(self.archive, comment="second")
        output = await self.api.info(self.archive, json=True)
        comment = output["archives"][0]["comment"]
        self.assertEqual(comment, "second", "Archive comment not updated")

    async def test_03_remove_file(self):
        """Change archive comment."""
        await self.api.create(self.archive, self.data)
        with open(self.file_3, "w+") as fp:
            fp.write("New Data")
        archive_2 = f"{self.repo}::2"
        await self.api.create(archive_2, self.data)
        await self.api.recreate(self.repo, exclude=self.file_2)
        first = await self.api.list(self.archive, json_lines=True)
        infirst = [v for v in first if v["path"] == self.file_2]
        self.assertEqual(len(first), 2, "Incorrect number of files in first archive.")
        self.assertEqual(len(infirst), 0, "Path removed from first archive.")
        second = await self.api.list(archive_2, json_lines=True)
        insecond = [v for v in first if v["path"] == self.file_2]
        self.assertEqual(len(second), 3, "Incorrect number of files in second archive.")
        self.assertEqual(len(insecond), 0, "Path removed from second archive.")
