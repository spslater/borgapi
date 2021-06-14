"""Test output stuff"""
import io
import logging
import unittest
from os import getenv, remove
from os.path import join
from time import sleep

from borgapi import BorgAPI

from .test_borgapi import BorgapiTests


class OutputTests(BorgapiTests):
    """Output tests commands"""

    @classmethod
    def setUpClass(cls):
        """setup logger stuff"""
        super().setUpClass()

        cls.api = BorgAPI()

        formatter = logging.Formatter("%(message)s")

        cls.list_handler = logging.StreamHandler(io.StringIO())
        cls.list_handler.setFormatter(formatter)
        cls.list_handler.setLevel("INFO")

        cls.stats_handler = logging.StreamHandler(io.StringIO())
        cls.stats_handler.setFormatter(formatter)
        cls.stats_handler.setLevel("INFO")

        list_logger = logging.getLogger("borg.output.list")
        list_logger.addHandler(cls.list_handler)

        stats_logger = logging.getLogger("borg.output.stats")
        stats_logger.addHandler(cls.stats_handler)

        cls.archive = f"{cls.repo}::1"

    @classmethod
    def tearDownClass(cls):
        """teardown logger stuff"""
        super().tearDownClass()

        cls.list_handler.stream.close()
        cls.stats_handler.stream.close()

    def setUp(self):
        """setup"""
        super().setUp()

        self.reset_stream(self.list_handler)
        self.reset_stream(self.stats_handler)

        self.api.init(self.repo)

    @staticmethod
    def display(header, output):
        """display captured output"""
        if getenv("BORGAPI_TEST_OUTPUT_DISPLAY"):
            print(header)
            for name, value in output.items():
                print(f"~~~~~~~~~~ {name} ~~~~~~~~~~")
                print(value)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print()

    @staticmethod
    def reset_stream(handler):
        """Get value from a stream and clear it"""
        handler.stream.close()
        handler.setStream(io.StringIO())

    @staticmethod
    def get_value(handler):
        """Get value from stream"""
        return handler.stream.getvalue()

    def test_create_1(self):
        """Stats log, List log"""
        output = self.api.create(self.archive, self.data, stats=True, list=True)
        self.display("create 1", output)
        self.assertType(output["stats"], str)
        self.assertType(output["list"], str)

    def test_create_2(self):
        """Stats json, List log"""
        output = self.api.create(self.archive, self.data, json=True, list=True)
        self.display("create 2", output)
        self.assertType(output["stats"], dict)
        self.assertType(output["list"], str)

    def test_create_3(self):
        """Stat to log, list to json"""
        output = self.api.create(
            self.archive,
            self.data,
            stats=True,
            log_json=True,
            list=True,
        )
        self.display("create 3", output)
        self.assertType(output["stats"], str)
        self.assertAnyType(output["list"], list, dict)

    def test_extract_1(self):
        """list to log"""
        self.api.create(self.archive, self.data)
        output = self.api.extract(self.archive, list=True, dry_run=True)
        self.display("extract 1", output)
        self.assertType(output["list"], str)

    def test_extract_2(self):
        """list to json"""
        self.api.create(self.archive, self.data)
        output = self.api.extract(self.archive, log_json=True, list=True, dry_run=True)
        self.display("extract 2", output)
        self.assertAnyType(output["list"], str)

    def test_list_1(self):
        """repo list"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.repo)
        self.display("list 1", output)
        self.assertType(output["list"], str)

    def test_list_2(self):
        """repo list short"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.repo, short=True)
        self.display("list 2", output)
        self.assertType(output["list"], str)

    def test_list_3(self):
        """repo list json"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.repo, json=True)
        self.display("list 3 - json", output)
        self.assertAnyType(output["list"], list, dict)
        output = self.api.list(self.repo, log_json=True)
        self.display("list 3 - log json", output)
        self.assertAnyType(output["list"], str)

    def test_list_4(self):
        """archive list"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.archive)
        self.display("list 4", output)
        self.assertType(output["list"], str)

    def test_list_5(self):
        """archive list short"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.archive, short=True)
        self.display("list 5", output)
        self.assertType(output["list"], str)

    def test_list_6(self):
        """archive list json"""
        self.api.create(self.archive, self.data)
        output = self.api.list(self.archive, json_lines=True)
        self.display("list 6", output)
        self.assertAnyType(output["list"], list, dict)

    def test_diff_1(self):
        """no flags"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2")
        self.display("diff 1", output)
        self.assertType(output["diff"], str)

    def test_diff_2(self):
        """json lines"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", json_lines=True)
        self.display("diff 2", output)
        self.assertAnyType(output["diff"], list, dict)

    def test_diff_3(self):
        """log json"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        output = self.api.diff(self.archive, "2", log_json=True)
        self.display("diff 3", output)
        self.assertAnyType(output["diff"], str)

    def test_delete_1(self):
        """archvie stats"""
        self.api.create(self.archive, self.data)
        output = self.api.delete(self.archive, stats=True)
        self.display("delete 1", output)
        self.assertType(output["stats"], str)

    def test_delete_2(self):
        """archvie stats"""
        self.api.create(self.archive, self.data)
        output = self.api.delete(self.archive, stats=True, log_json=True)
        self.display("delete 2", output)
        self.assertType(output["stats"], str)

    def _prune_setup(self):
        self.api.create(self.archive, self.data)
        sleep(1)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        sleep(1)
        remove(self.file_1)
        self.api.create(f"{self.repo}::3", self.data)
        sleep(1)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_1_text)
        self.api.create(f"{self.repo}::4", self.data)
        sleep(1)
        remove(self.file_2)
        self.api.create(f"{self.repo}::5", self.data)
        sleep(1)

    def test_prune_1(self):
        """list"""
        self._prune_setup()
        output = self.api.prune(self.repo, keep_last="3", dry_run=True, list=True)
        self.display("prune 1", output)
        self.assertType(output["list"], str)

    def test_prune_2(self):
        """stats"""
        self._prune_setup()
        output = self.api.prune(self.repo, keep_last="3", dry_run=True, stats=True)
        self.display("prune 2", output)
        self.assertType(output["stats"], str)

    def test_info_1(self):
        """repo no flags"""
        output = self.api.info(self.repo, log_json=True)
        self.display("info 1", output)
        self.assertType(output["info"], str)

    def test_info_2(self):
        """repo json"""
        output = self.api.info(self.repo, json=True)
        self.display("info 2", output)
        self.assertAnyType(output["info"], list, dict)

    def test_info_3(self):
        """archive no flags"""
        self.api.create(self.archive, self.data)
        output = self.api.info(self.archive)
        self.display("info 3", output)
        self.assertType(output["info"], str)

    def test_info_4(self):
        """archive json"""
        self.api.create(self.archive, self.data)
        output = self.api.info(self.archive, json=True)
        self.display("info 4", output)
        self.assertAnyType(output["info"], list, dict)

    def test_export_tar_1(self):
        """list"""
        export_dir = join(self.temp, "export")
        self._make_clean(export_dir)
        tar_file = join(export_dir, "export.tar")
        self.api.create(self.archive, self.data)
        output = self.api.export_tar(self.archive, tar_file, list=True)
        self.display("export tar 1", output)
        self.assertType(output["list"], str)

    def test_export_tar_2(self):
        """stdout"""
        self.api.create(self.archive, self.data)
        output = self.api.export_tar(self.archive, "-")
        self.display("export tar 2", output)
        self.assertType(output["tar"], bytes)

    def test_config_1(self):
        """list"""
        output = self.api.config(self.repo, list=True)
        self.display("config 1", output)
        self.assertType(output["list"], str)

    def test_config_2(self):
        """value"""
        output = self.api.config(self.repo, "max_segment_size")
        self.display("config 2", output)
        self.assertType(output["changes"], list)

    @unittest.skipIf(
        getenv("BORGAPI_TEST_BENCHMARK_SKIP"),
        "Gotta go fast (only use for quick testing, not release)",
    )
    def test_benchmark_crud_1(self):
        """output"""
        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        output = self.api.benchmark_crud(self.repo, benchmark_dir)
        self.display("benchmark crud 1", output)
        self.assertType(output["benchmark"], str)
