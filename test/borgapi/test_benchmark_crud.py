"""Test benchmarck crud command"""
from os import getenv
from os.path import join
from shutil import rmtree

from .test_borgapi import BorgapiTests


class BenchmarkCrudTests(BorgapiTests):
    """Benchmark Crud command tests"""

    def setUp(self):
        if getenv("BORGAPI_TEST_BENCHMARK_SKIP"):
            self.skipTest("Gotta go fast (only use for quick testing, not release)")
        super().setUp()

    def test_output(self):
        """Benchmark CRUD operations"""
        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        output = self.api.benchmark_crud(self.repo, benchmark_dir)
        self._display("benchmark crud", output)
        self.assertType(output, str)
        rmtree(benchmark_dir)
