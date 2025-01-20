# ruff: noqa: N802
"""Test BorgAPI module."""

import unittest
from configparser import ConfigParser
from os import getenv, makedirs, remove
from os.path import exists, join
from shutil import rmtree

from dotenv import load_dotenv

from borgapi import BorgAPI, BorgAPIAsync


class BorgapiTests(unittest.TestCase):
    """Test for the borgbackup api."""

    @staticmethod
    def assertFileExists(path, msg=None):
        """Assert if a path exists or not."""
        if not exists(path):
            raise AssertionError(msg or f"{path} does not exist")

    @staticmethod
    def assertFileNotExists(path, msg=None):
        """Assert if a path exists or not."""
        if exists(path):
            raise AssertionError(msg or f"{path} does exist")

    @staticmethod
    def assertKeyExists(key, dictionary, msg=None):
        """Assert a key exists in a dictionary."""
        if key not in dictionary:
            raise AssertionError(msg or f"{key} does not exist in dictionary")

    @staticmethod
    def assertKeyNotExists(key, dictionary, msg=None):
        """Assert a key does not exist in a dictionary."""
        if key in dictionary:
            raise AssertionError(msg or f"{key} exists in dictionary")

    @staticmethod
    def assertType(obj, type_, msg=None):
        """Assert an object is an instance of type."""
        if not isinstance(obj, type_):
            raise AssertionError(msg or f"{obj} is not type {type_}, it is {type(obj)}")

    @staticmethod
    def assertAnyType(obj, *types, msg=None):
        """Assert an object is an instance of type."""
        if not any([isinstance(obj, t) for t in types]):
            raise AssertionError(msg or f"{obj} is not any of {types}; it is {type(obj)}")

    @staticmethod
    def assertSubclass(obj, class_, msg=None):
        """Assert an object is an subclass of class."""
        if not issubclass(obj, class_):
            raise AssertionError(msg or f"{obj} is not a subtype of {class_}")

    @staticmethod
    def assertNone(obj, msg=None):
        """Assert an object is None."""
        if obj is not None:
            raise AssertionError(msg or f"Value is not None: {obj}")

    @staticmethod
    def assertNotNone(obj, msg=None):
        """Assert an object is None."""
        if obj is None:
            raise AssertionError(msg or "Value is None")

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
    def _read_config(string=None, filename=None):
        """Convert config string into dictionary."""
        config = ConfigParser()
        if filename:
            with open(filename, "r") as fp:
                config.read_file(fp)
        else:
            config.read_string(string)
        return config

    @staticmethod
    def _display(header, output, single=True):
        """Display captured output."""
        if getenv("BORGAPI_TEST_OUTPUT_DISPLAY"):
            print(header)
            if single:
                print(output)
            else:
                for name, value in output.items():
                    print(f"~~~~~~~~~~ {name} ~~~~~~~~~~")
                    print(value)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print()

    @classmethod
    def setUpClass(cls):
        """Init environment for borg use."""
        cls.temp = "test/temp"
        cls.data = join(cls.temp, "data")
        cls.repo = join(cls.temp, "repo")
        cls.logs = join(cls.temp, "logs")

        cls.archive = f"{cls.repo}::1"

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
        """Remove temp directory."""
        if not getenv("BORGAPI_TEST_KEEP_LOGS") and not getenv("BORGAPI_TEST_KEEP_TEMP"):
            cls._try_pass(FileNotFoundError, rmtree, cls.temp)
            cls._try_pass(OSError, rmtree, cls.temp)

    def _setUp(self):
        self._try_pass(FileExistsError, makedirs, self.temp)
        self._try_pass(FileExistsError, makedirs, self.data)
        self._try_pass(FileExistsError, makedirs, self.repo)
        self._try_pass(FileExistsError, makedirs, self.logs)

        with open(self.file_1, "w") as fp:
            fp.write(self.file_1_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_2_text)

        self._try_pass(FileNotFoundError, remove, self.file_3)

    def setUp(self):
        """Init files data."""
        self._setUp()

        self.api = BorgAPI()
        self.api.init(self.repo)

    def tearDown(self):
        """Reset mess made."""
        if not getenv("BORGAPI_TEST_KEEP_TEMP"):
            self._try_pass(FileNotFoundError, rmtree, self.data)
            self._try_pass(OSError, rmtree, self.repo)
            self._try_pass(FileNotFoundError, rmtree, self.repo)
            if not getenv("BORGAPI_TEST_KEEP_LOGS"):
                self._try_pass(FileNotFoundError, rmtree, self.logs)
                self._try_pass(OSError, rmtree, self.temp)
                self._try_pass(FileNotFoundError, rmtree, self.temp)

    def _create_default(self):
        self.api.create(self.archive, self.data)


class BorgapiAsyncTests(unittest.IsolatedAsyncioTestCase, BorgapiTests):
    """Test for the borgbackup api with async methods."""

    def setUp(self):
        """Init files data."""
        self._setUp()

    async def asyncSetUp(self):
        """Init files data for async use."""
        self.api = BorgAPIAsync()
        await self.api.init(self.repo)

    async def _create_default(self):
        await self.api.create(self.archive, self.data)
