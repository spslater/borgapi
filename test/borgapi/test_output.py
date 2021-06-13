"""Test output stuff"""
import logging
import io
import unittest
from os import getenv, remove
from os.path import join
from shutil import rmtree
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
    def display(header, *outputs):
        """display captured output"""
        if getenv("BORGAPI_TEST_OUTPUT_DISPLAY"):
            print(header)
            for name, value in outputs:
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
        out, err = self.api.create(self.archive, self.data, stats=True, list=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "create 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, string
        self.assertTrue(stats_capture) # stats, string

    def test_create_2(self):
        """Stats json, List log"""
        out, err = self.api.create(self.archive, self.data, json=True, list=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "create 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # stats, json
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, string
        self.assertFalse(stats_capture)

    def test_create_3(self):
        """Stat to log, list to json"""
        out, err = self.api.create(
            self.archive,
            self.data,
            stat=True,
            log_json=True,
            list=True,
        )

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "create 3",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out) # stats list, not shown because log_json
        self.assertTrue(err) # list, string
        self.assertFalse(list_capture) # ??? log_json / list
        self.assertFalse(stats_capture) # ??? log_json

    def test_extract_1(self):
        """list to log"""
        self.api.create(self.archive, self.data)
        out, err = self.api.extract(self.archive, list=True, dry_run=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "extract 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, string
        self.assertFalse(stats_capture)

    def test_extract_2(self):
        """list to json"""
        self.api.create(self.archive, self.data)
        out, err = self.api.extract(self.archive, log_json=True, list=True, dry_run=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "extract 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, json
        self.assertFalse(stats_capture)

    def test_list_1(self):
        """repo list"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.repo)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_list_2(self):
        """repo list short"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.repo, short=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_list_3(self):
        """repo list json"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.repo, json=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 3 - json",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

        out, err = self.api.list(self.repo, log_json=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 3 - log json",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_list_4(self):
        """archive list"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.archive)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 4",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_list_5(self):
        """archive list short"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.archive, short=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 5",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_list_6(self):
        """archive list json"""
        self.api.create(self.archive, self.data)
        out, err = self.api.list(self.archive, json_lines=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "list 6",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # list, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_diff_1(self):
        """no flags"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        out, err = self.api.diff(self.archive, "2")

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "diff 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # diff, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_diff_2(self):
        """json lines"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        out, err = self.api.diff(self.archive, "2", json_lines=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "diff 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # diff, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_diff_3(self):
        """log json"""
        self.api.create(self.archive, self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        self.api.create(f"{self.repo}::2", self.data)
        out, err = self.api.diff(self.archive, "2", log_json=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "diff 3",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # diff, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_delete_1(self):
        """repo no flags"""
        self.api.create(self.archive, self.data)
        out, err = self.api.delete(self.repo, dry_run=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "delete 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertTrue(err) # confirmation message
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_delete_2(self):
        """archvie no flags"""
        self.api.create(self.archive, self.data)
        out, err = self.api.delete(self.archive, dry_run=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "delete 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_delete_3(self):
        """archvie stats"""
        self.api.create(self.archive, self.data)
        out, err = self.api.delete(self.archive, stats=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "delete 3",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertTrue(stats_capture) # stats, string

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
        out, err = self.api.prune(self.repo, keep_last="3", dry_run=True, list=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "prune 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, string
        self.assertFalse(stats_capture)

    def test_prune_2(self):
        """stats"""
        self._prune_setup()
        out, err = self.api.prune(self.repo, keep_last="3", dry_run=True, stats=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "prune 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertTrue(stats_capture) # stats, string

    def test_info_1(self):
        """repo no flags"""
        out, err = self.api.info(self.repo)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "info 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # info, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_info_2(self):
        """repo json"""
        out, err = self.api.info(self.repo, json=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "info 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # info, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_info_3(self):
        """archive no flags"""
        self.api.create(self.archive, self.data)
        out, err = self.api.info(self.archive)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "info 3",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # info, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_info_4(self):
        """archive json"""
        self.api.create(self.archive, self.data)
        out, err = self.api.info(self.archive, json=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "info 4",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # info, json
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_export_tar_1(self):
        """list"""
        export_dir = join(self.temp, "export")
        self._make_clean(export_dir)
        tar_file = join(export_dir, "export.tar")

        self.api.create(self.archive, self.data)

        out, err = self.api.export_tar(self.archive, tar_file, list=True)

        rmtree(export_dir)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "export tar 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertFalse(out)
        self.assertFalse(err)
        self.assertTrue(list_capture) # list, string
        self.assertFalse(stats_capture)

    @unittest.skip("Wait to merge bug-12")
    def test_export_tar_2(self):
        """stdout"""
        self.api.create(self.archive, self.data)

        out, err = self.api.export_tar(self.archive, "-")

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "export tar 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # tar, bytes
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_config_1(self):
        """list"""
        out, err = self.api.config(self.repo, list=True)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "config 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # config, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    def test_config_2(self):
        """value"""
        out, err = self.api.config(self.repo, "max_segment_size")

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "config 2",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # config, string
        self.assertTrue(err) # config, [None]
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)

    @unittest.skipIf(
        getenv("BORGAPI_TEST_BENCHMARK_SKIP"),
        "Gotta go fast (only use for quick testing, not release)",
    )
    def test_benchmark_crud_1(self):
        """output"""
        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        out, err = self.api.benchmark_crud(self.repo, benchmark_dir)

        rmtree(benchmark_dir)

        list_capture = self.get_value(self.list_handler)
        stats_capture = self.get_value(self.stats_handler)

        self.display(
            "benchmark crud 1",
            ("list", list_capture),
            ("stats", stats_capture),
            ("stdout", out),
            ("stderr", err),
        )

        self.assertTrue(out) # results, string
        self.assertFalse(err)
        self.assertFalse(list_capture)
        self.assertFalse(stats_capture)
