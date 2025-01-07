"""Test deff command."""

from . import BorgapiAsyncTests, BorgapiTests


class DiffTests(BorgapiTests):
    """Diff command tests."""

    def setUp(self):
        """Prepare data for diff tests."""
        super().setUp()
        self._create_default()

    def test_01_add_file(self):
        """Diff new file."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", json_lines=True)
        self.assertType(output, list)
        self.assertGreaterEqual(len(output), 2)
        changes = set()
        for out in output:
            changes.add(out["changes"][0]["type"])
        self.assertIn("added", changes, "New file not listed as added")

    def test_02_modify_file(self):
        """Diff modified file."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", json_lines=True, sort=True)
        self.assertType(output, list)
        modded_2 = None
        for out in output:
            if out["path"] == self.file_2:
                modded_2 = out
                break
        if modded_2 is None:
            raise AssertionError("File expected to change, but did not")
        modify_type = modded_2["changes"][0]["type"]
        self.assertEqual(modify_type, "modified", "Unexpected change type")

    def test_03_output(self):
        """Diff string."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2")
        self._display("diff sting", output)
        self.assertType(output, str)

    def test_04_output_json(self):
        """Diff json."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", log_json=True)
        self._display("diff log json", output)
        self.assertAnyType(output, str)


class DiffAsyncTests(BorgapiAsyncTests):
    """Diff command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async diff tests."""
        await super().asyncSetUp()
        await self._create_default()

    async def test_01_add_file(self):
        """Diff new file."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        await self.api.create(f"{self.repo}::2", self.data)
        output = await self.api.diff(self.archive, "2", json_lines=True)
        self.assertType(output, list)
        self.assertGreaterEqual(len(output), 2)
        changes = set()
        for out in output:
            changes.add(out["changes"][0]["type"])
        self.assertIn("added", changes, "New file not listed as added")

    async def test_02_modify_file(self):
        """Diff modified file."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        await self.api.create(f"{self.repo}::2", self.data)
        output = await self.api.diff(self.archive, "2", json_lines=True, sort=True)
        self.assertType(output, list)
        modded_2 = None
        for out in output:
            if out["path"] == self.file_2:
                modded_2 = out
                break
        if modded_2 is None:
            raise AssertionError("File expected to change, but did not")
        modify_type = modded_2["changes"][0]["type"]
        self.assertEqual(modify_type, "modified", "Unexpected change type")

    async def test_03_output(self):
        """Diff string."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        await self.api.create(f"{self.repo}::2", self.data)
        output = await self.api.diff(self.archive, "2")
        self._display("diff sting", output)
        self.assertType(output, str)

    async def test_04_output_json(self):
        """Diff json."""
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        await self.api.create(f"{self.repo}::2", self.data)
        output = await self.api.diff(self.archive, "2", log_json=True)
        self._display("diff log json", output)
        self.assertAnyType(output, str)
