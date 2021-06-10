"""Test borgapi module"""
import logging
import unittest
from configparser import ConfigParser
from os import getenv, makedirs, remove
from os.path import exists, join
from shutil import rmtree
from time import sleep

from borg.archive import Archive
from borg.repository import Repository
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
        load_dotenv("test/res/test_env")

        cls.temp = "test/temp"
        cls.data = join(cls.temp, "data")
        cls.repo = join(cls.temp, "repo")
        cls.logs = join(cls.temp, "logs")

        cls._try_pass(FileNotFoundError, rmtree, cls.data)
        cls._try_pass(FileNotFoundError, rmtree, cls.repo)
        cls._try_pass(FileNotFoundError, rmtree, cls.logs)

        cls.file_1 = join(cls.data, "file_1.txt")
        cls.file_1_text = "Hello World"
        cls.file_2 = join(cls.data, "file_2.txt")
        cls.file_2_text = "Goodbye Fools"
        cls.file_3 = join(cls.data, "file_3.txt")
        cls.file_3_text = "New File Added"

    @classmethod
    def tearDownClass(cls):
        """Remove temp directory"""
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
        self._try_pass(FileNotFoundError, rmtree, self.data)
        self._try_pass(FileNotFoundError, rmtree, self.repo)
        self._try_pass(FileNotFoundError, rmtree, self.logs)

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

    def test_init(self):
        """Initalize new repository"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertFileExists(join(self.repo, "README"))

    def test_init_already_exists(self):
        """Initalize a repo in a directory where one already exists"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertRaises(
            Repository.AlreadyExists,
            api.init,
            self.repo,
            msg="Duplicate repositroy overwrites old repo",
        )

    def test_init_path_exists(self):
        """Initalize a repo in a directory where other data exists"""
        api = BorgAPI()
        api.init(self.repo)
        self.assertRaises(
            Repository.PathAlreadyExists,
            api.init,
            self.data,
            msg="Repositroy overwrites directory with other data",
        )

    def test_list(self):
        """List repo archvies and archive files"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.list(self.repo, json=True)
        num_archvies = len(out["archives"])
        self.assertEqual(num_archvies, 1, "Unexpected number of archives returned")

        out, _ = api.list(f"{self.repo}::1", json_lines=True)
        num_files = len(out)
        self.assertEqual(num_files, 3, "Unexpected number of files returned")

    def test_create(self):
        """Create new archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        out, _ = api.list(self.repo, json=True)
        num_archives = len(out["archives"])
        self.assertEqual(num_archives, 1, "Archive not saved")
        archive_name = out["archives"][0]["name"]
        self.assertEqual(archive_name, "1", "Archive name does not match set name")

    def test_create_second(self):
        """Create second archive after data modification"""
        api = self._init_and_create(self.repo, "1", self.data)

        with open(self.file_3, "w+") as fp:
            fp.write("New Data")
        api.create(f"{self.repo}::2", self.data)

        out, _ = api.list(self.repo, json=True)
        num_archives = len(out["archives"])
        self.assertEqual(num_archives, 2, "Multiple archives not saved")
        archive_1_name = out["archives"][0]["name"]
        self.assertEqual(archive_1_name, "1", "Archive name does not match set name")
        archive_2_name = out["archives"][1]["name"]
        self.assertEqual(archive_2_name, "2", "Archive name does not match set name")

    def test_create_already_exists(self):
        """Create an archive with an existing name"""
        api = self._init_and_create(self.repo, "1", self.data)

        self.assertRaises(
            Archive.AlreadyExists,
            api.create,
            f"{self.repo}::1",
            self.data,
        )

    def test_extract(self):
        """Extract file"""
        api = self._init_and_create(self.repo, "1", self.data)

        remove(self.file_1)
        self.assertFileNotExists(self.file_1)

        api.extract(f"{self.repo}::1", self.file_1)
        self.assertFileExists(self.file_1)

    def test_extract_not_exist(self):
        """Extract path that does not exist"""
        api = self._init_and_create(self.repo, "1", self.data)

        with self.assertLogs("borg", "WARNING") as logger:
            api.extract(f"{self.repo}::1", self.file_3)
        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?file_3.*never",
            "Warning not logged for bad path",
        )

    @unittest.skip(
        "BUG: Captured output uses StringIO which has no buffer like sys.stdout does"
    )
    def test_extract_stdout(self):
        """Capture Extracted File"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.extract(f"{self.repo}::1", self.file_1, stdout=True)
        self.assertEqual(out, self.file_1_text, "Extracted file text does not match")

    def test_check(self):
        """Check archive / repository integrity"""
        api = self._init_and_create(self.repo, "1", self.data)

        with self.assertLogs("borg.repository", "INFO") as repository, self.assertLogs(
            "borg.archive", "INFO"
        ) as archive:
            api.check(self.repo)
        self.assertGreater(len(repository.records), 0, "Repository check not run")
        self.assertGreater(len(archive.records), 0, "Archive check not run")

    def test_rename(self):
        """Rename a archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        out, _ = api.list(self.repo, json=True)
        original_name = out["archives"][0]["name"]
        api.rename(f"{self.repo}::1", "2")
        out, _ = api.list(self.repo, json=True)
        new_name = out["archives"][0]["name"]
        self.assertNotEqual(new_name, original_name, "Name change did not occur")
        self.assertEqual(new_name, "2", "Name did not change to expected output")

    def test_rename_no_exist(self):
        """Rename nonexistant archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        self.assertRaises(
            Archive.DoesNotExist,
            api.rename,
            f"{self.repo}::2",
            "3",
            msg="Renamed archive that does not exist",
        )

    def test_diff_add_file(self):
        """Diff two archives"""
        api = self._init_and_create(self.repo, "1", self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::2", self.data)
        out, _ = api.diff(f"{self.repo}::1", "2", json_lines=True)
        modify_path = out["path"]
        modify_type = out["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_3, "Unexpected new filename")
        self.assertEqual(modify_type, "added", "New file not listed as added")

    def test_diff_modify_file(self):
        """File diff of two archives"""
        api = self._init_and_create(self.repo, "1", self.data)
        with open(self.file_3, "w") as fp:
            fp.write(self.file_3_text)
        with open(self.file_2, "w") as fp:
            fp.write(self.file_3_text)
        api.create(f"{self.repo}::2", self.data)
        out, _ = api.diff(f"{self.repo}::1", "2", json_lines=True, sort=True)
        modify_path = out[0]["path"]
        modify_type = out[0]["changes"][0]["type"]
        self.assertEqual(modify_path, self.file_2, "Unexpected file changed")
        self.assertEqual(modify_type, "modified", "Unexpected change type")

    def test_delete_repository(self):
        """Delete repository"""
        api = self._init_and_create(self.repo, "1", self.data)
        api.delete(self.repo)
        self.assertRaises(
            Repository.DoesNotExist,
            api.list,
            self.repo,
            msg="Deleted repository still exists",
        )

    def test_delete_repository_not_exist(self):
        """Delete repository that doesn't exist"""
        api = BorgAPI()
        self.assertRaises(
            Repository.InvalidRepository,
            api.delete,
            self.repo,
            msg="Deleted nonexistant repository",
        )

    def test_delete_archive(self):
        """Delete archive"""
        api = self._init_and_create(self.repo, "1", self.data)
        api.delete(f"{self.repo}::1")
        self.assertRaises(
            Archive.DoesNotExist,
            api.list,
            f"{self.repo}::1",
            msg="Deleted archive still exists",
        )

    def test_delete_archive_not_exist(self):
        """Delete archvie that doesn't exist"""
        api = self._init_and_create(self.repo, "1", self.data)

        with self.assertLogs("borg", "WARNING") as logger:
            api.delete(f"{self.repo}::2")

        message = logger.records[0].getMessage()
        self.assertRegex(
            message,
            r".*?2.*not found",
            "Warning not logged for bad archive name",
        )

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

    def test_info_repository(self):
        """Repository info"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.info(self.repo, json=True)
        self.assertKeyExists("cache", out)
        self.assertKeyNotExists("archives", out)

    def test_info_archive(self):
        """Archive info"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.info(f"{self.repo}::1", json=True)
        self.assertKeyExists("cache", out)
        self.assertKeyExists("archives", out)

    def test_mount_umount_archive(self):
        """Mount and unmount a archive"""
        api = self._init_and_create(self.repo, "1", self.data)

        mount = join(self.temp, "mount")
        self._make_clean(mount)
        api.mount(self.repo, mount)

        file_1_mount = join(mount, "1", self.file_1)
        self.assertFileExists(file_1_mount)

        rmtree(mount)

    def test_mount_umount_repository(self):
        """Mount and unmount a repository"""
        api = self._init_and_create(self.repo, "1", self.data)

        mount = join(self.temp, "mount")
        self._make_clean(mount)
        api.mount(f"{self.repo}::1", mount)

        file_1_mount = join(mount, self.file_1)
        self.assertFileExists(file_1_mount)

        rmtree(mount)

    def test_key_change_passphrase(self):
        """Change key passphrase"""
        api = self._init_and_create(self.repo, "1", self.data)

        repo_config_file = join(self.repo, "config")
        repo_config = ConfigParser()
        with open(repo_config_file, "r") as fp:
            repo_config.read_file(fp)
        original_value = repo_config["repository"]["key"]

        api.set_environ(dictionary={"BORG_NEW_PASSPHRASE": "newpass"})
        api.key_change_passphrase(self.repo)
        api.unset_environ("BORG_NEW_PASSPHRASE")

        with open(repo_config_file, "r") as fp:
            repo_config.read_file(fp)
        key_change_value = repo_config["repository"]["key"]

        self.assertNotEqual(
            key_change_value,
            original_value,
            "Changed key matches original",
        )

    def test_key_export(self):
        """Export repo excryption key"""
        api = self._init_and_create(self.repo, "1", self.data)

        export_dir = join(self.temp, "export")
        key_file = join(export_dir, "key.txt")
        self._make_clean(export_dir)
        api.key_export(self.repo, key_file)

        self.assertFileExists(key_file, "Repo key not exported to expected location")
        rmtree(export_dir)

    def test_key_import(self):
        """Import original key to repository"""
        api = self._init_and_create(self.repo, "1", self.data)

        export_dir = join(self.temp, "export")
        self._make_clean(export_dir)
        key_file = join(export_dir, "key.txt")
        api.key_export(self.repo, key_file)

        repo_config_file = join(self.repo, "config")
        repo_config = ConfigParser()
        with open(repo_config_file, "r") as fp:
            repo_config.read_file(fp)
        original_value = repo_config["repository"]["key"]

        api.key_import(self.repo, key_file)

        with open(repo_config_file, "r") as fp:
            repo_config.read_file(fp)
        restored_value = repo_config["repository"]["key"]

        self.assertEqual(
            restored_value,
            original_value,
            "Restored key does not match original",
        )

        rmtree(export_dir)

    def test_export_tar(self):
        """Export tar file"""
        api = self._init_and_create(self.repo, "1", self.data)

        export_dir = join(self.temp, "export")
        self._make_clean(export_dir)
        tar_file = join(export_dir, "export.tar")

        api.export_tar(f"{self.repo}::1", tar_file)
        self.assertFileExists(tar_file, "Tar file not exported")

        rmtree(export_dir)

    def test_config_list(self):
        """List config values for repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        out, _ = api.config(self.repo, list=True)

        repo_config = ConfigParser()
        repo_config.read_string(out)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "0", "Unexpected config value")

        out, _ = api.config(self.repo, "additional_free_space")
        self.assertEqual(out[0], "0", "Unexpected config value")

    def test_config_change(self):
        """Change config values in repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.config(self.repo, ("append_only", "1"))
        out, _ = api.config(self.repo, list=True)
        repo_config = ConfigParser()
        repo_config.read_string(out)
        append_only = repo_config["repository"]["append_only"]
        self.assertEqual(append_only, "1", "Unexpected config value")

    def test_config_delete(self):
        """Delete config value from repo"""
        api = self._init_and_create(self.repo, "1", self.data)

        api.config(self.repo, "additional_free_space", delete=True)
        out, _ = api.config(self.repo, list=True)
        repo_config = ConfigParser()
        repo_config.read_string(out)
        additional_free_space = repo_config["repository"]["additional_free_space"]
        self.assertEqual(additional_free_space, "False", "Unexpected config value")

    @unittest.skip("WIP: Don't know what locking would be used for")
    def test_lock(self):
        """Don't know what locking would be used for, so don't know how to test"""

    def test_benchmark_crud(self):
        """Benchmark CRUD operations"""
        api = self._init_and_create(self.repo, "1", self.data)

        benchmark_dir = join(self.temp, "benchmark")
        self._make_clean(benchmark_dir)

        out, _ = api.benchmark_crud(self.repo, benchmark_dir)
        self.assertTrue(out, "Unexpected (ie None) output from benchmark")

        rmtree(benchmark_dir)
