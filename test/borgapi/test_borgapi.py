"""Test borgapi module"""
import logging
import unittest
from configparser import ConfigParser
from os import getenv, makedirs, remove
from os.path import exists, join
from shutil import rmtree
from time import sleep

from dotenv import load_dotenv

from borgapi import BorgAPI


# pylint: disable=too-many-public-methods
class BorgapiTests(unittest.TestCase):
    """Test for the borgbackup api"""

    # pylint: disable=invalid-name
    @staticmethod
    def assertFileExists(path, msg=None):
        """Assert if a path exists or not"""
        if not exists(path):
            raise AssertionError(msg or f"{path} does not exist")

    @staticmethod
    def assertFileNotExists(path, msg=None):
        """Assert if a path exists or not"""
        if exists(path):
            raise AssertionError(msg or f"{path} does exist")

    @staticmethod
    def assertKeyExists(key, dictionary, msg=None):
        """Assert a key exists in a dictionary"""
        if key not in dictionary:
            raise AssertionError(msg or f"{key} does not exist in dictionary")

    @staticmethod
    def assertKeyNotExists(key, dictionary, msg=None):
        """Assert a key does not exist in a dictionary"""
        if key in dictionary:
            raise AssertionError(msg or f"{key} exists in dictionary")

    @staticmethod
    def _try_pass(error, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except error:
            pass

    @staticmethod
    def _make_clean(directory):
        try:
            makedirs(directory)
        except FileExistsError:
            rmtree(directory)
            makedirs(directory)

    @staticmethod
    def read_config(string=None, filename=None):
        """Convert config string into dictionary"""
        config = ConfigParser()
        if filename:
            with open(filename, "r") as fp:
                config.read_file(fp)
        else:
            config.read_string(string)
        return config

    # pylint: disable=dangerous-default-value
    @staticmethod
    def _init_and_create(repo, archive, data, options={}):
        api = BorgAPI(options=options)
        api.init(repo, **options)
        api.create(f"{repo}::{archive}", data, **options)
        return api

    @classmethod
    def setUpClass(cls):
        """Initalize environment for borg use"""

        cls.temp = "test/temp"
        cls.data = join(cls.temp, "data")
        cls.repo = join(cls.temp, "repo")
        cls.logs = join(cls.temp, "logs")

        cls._try_pass(FileNotFoundError, rmtree, cls.data)
        cls._try_pass(FileNotFoundError, rmtree, cls.repo)
        if not getenv("BORGAPI_TEST_KEEP_LOGS"):
            cls._try_pass(FileNotFoundError, rmtree, cls.logs)

        cls.file_1 = join(cls.data, "file_1.txt")
        cls.file_1_text = "Hello World"
        cls.file_2 = join(cls.data, "file_2.txt")
        cls.file_2_text = "Goodbye Fools"
        cls.file_3 = join(cls.data, "file_3.txt")
        cls.file_3_text = "New File Added"

        cls._try_pass(FileExistsError, makedirs, cls.data)
        cls._try_pass(FileExistsError, makedirs, cls.repo)
        cls._try_pass(FileExistsError, makedirs, cls.logs)
        load_dotenv("test/res/test_env")

    @classmethod
    def tearDownClass(cls):
        """Remove temp directory"""
        if not getenv("BORGAPI_TEST_KEEP_LOGS") and not getenv("BORGAPI_TEST_KEEP_TEMP"):
            cls._try_pass(FileNotFoundError, rmtree, cls.temp)

    def setUp(self):
        """Setup files data"""
        self._try_pass(FileExistsError, makedirs, self.data)
        self._try_pass(FileExistsError, makedirs, self.repo)
        self._try_pass(FileExistsError, makedirs, self.logs)

        with open(self.file_1, "w") as fp:
            fp.write(self.file_1_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_2_text)

        self._try_pass(FileNotFoundError, remove, self.file_3)

    def tearDown(self):
        """Resets mess made"""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            self._try_pass(FileNotFoundError, rmtree, self.data)
            self._try_pass(FileNotFoundError, rmtree, self.repo)
            if not getenv("BORGAPI_TEST_KEEP_LOGS"):
                self._try_pass(FileNotFoundError, rmtree, self.logs)


class SingleTests(BorgapiTests):
    """Simple Command and Class Methodss tests"""

    def test_borgapi_logger(self):
        """Verify loggers are setup correctly for borgapi"""
        BorgAPI()
        loggers = logging.root.manager.loggerDict
        self.assertIn("borgapi", loggers, "borgapi logger not present")
        self.assertIn("borg", loggers, "borg logger not present")

    def test_set_environ(self):
        """Set new env variable"""
        api = BorgAPI()

        key = "TEST_VARIABLE"

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        api.set_environ(filename=self.file_3)
        got = getenv(key)
        self.assertEqual(got, self.file_3_text)

        api.set_environ(dictionary={key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)

        api.set_environ(**{key: self.file_2_text})
        got = getenv(key)
        self.assertEqual(got, self.file_2_text)

    def test_unset_environ(self):
        """Remove env variable"""
        api = BorgAPI()

        key = "TEST_VARIABLE"

        api.set_environ(**{key: self.file_1_text})
        got = getenv(key)
        self.assertEqual(got, self.file_1_text)
        api.unset_environ(key)
        got = getenv(key)
        self.assertFalse(got)

        with open(self.file_3, "w") as fp:
            fp.write(f"{key}={self.file_3_text}")
        api.set_environ(filename=self.file_3)
        api.unset_environ()
        got = getenv(key)
        self.assertFalse(got)

    def test_prune(self):
        """Prune archives"""
        api = self._init_and_create(self.repo, "1", self.data)
        sleep(1)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::2", self.data)
        sleep(1)
        with open(self.file_1, "w") as fp:
            fp.write(self.file_2_text)
        api.create(f"{self.repo}::3", self.data)
        sleep(1)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::4", self.data)
        sleep(1)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_1_text)
        api.create(f"{self.repo}::5", self.data)
        sleep(1)

        api.prune(self.repo, keep_last="3")
        out, _ = api.list(self.repo, json=True)
        num_archives = len(out["archives"])
        self.assertEqual(num_archives, 3, "Unexpected number of archvies pruned")

    @unittest.skip("WIP: Don't know what locking would be used for")
    def test_lock(self):
        """Don't know what locking would be used for, so don't know how to test"""

    @unittest.skipIf(
        getenv("BORGAPI_TEST_BENCHMARK_SKIP"),
        "Gotta go fast (only use for quick testing, not release)",
    )
    def test_benchmark_crud(self):
        """Benchmark CRUD operations"""
        api = self._init_and_create(self.repo, "1", self.data)

        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)
        out, _ = api.benchmark_crud(self.repo, benchmark_dir)

        self.assertTrue(out, "Unexpected (ie None) output from benchmark")

        rmtree(benchmark_dir)
