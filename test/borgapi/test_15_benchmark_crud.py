"""Test benchmarck crud command."""

import unittest
from os import getenv
from os.path import join
from shutil import rmtree

from . import BorgapiAsyncTests, BorgapiTests


class BenchmarkCrudTests(BorgapiTests):
    """Benchmark Crud command tests."""

    def setUp(self):
        """Prepare data for benchmark crud tests."""
        if getenv("BORGAPI_TEST_BENCHMARK_SKIP"):
            self.skipTest("Gotta go fast (only use for quick testing, not release)")
        super().setUp()

    @unittest.skip("WIP: Keeps failing in Dropbox folder, but not regular folder")
    def test_01_output(self):
        """Benchmark CRUD operations."""
        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        output = self.api.benchmark_crud(self.repo, benchmark_dir)
        self._display("benchmark crud", output)
        self.assertType(output, str)
        rmtree(benchmark_dir)


class BenchmarkCrudAsyncTests(BorgapiAsyncTests):
    """Benchmark Crud command tests."""

    async def asyncSetUp(self):
        """Prepare async data for async benchmark crud tests."""
        if getenv("BORGAPI_TEST_BENCHMARK_SKIP"):
            self.skipTest("Gotta go fast (only use for quick testing, not release)")
        await super().asyncSetUp()

    @unittest.skip("WIP: Keeps failing in Dropbox folder, but not regular folder")
    async def test_01_output(self):
        """Benchmark CRUD operations."""
        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        output = await self.api.benchmark_crud(self.repo, benchmark_dir)
        self._display("benchmark crud", output)
        self.assertType(output, str)
        rmtree(benchmark_dir)
