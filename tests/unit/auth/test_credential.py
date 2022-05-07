import copy
import pathlib
import shutil
import tempfile
import time
import unittest

# TODO: See comments in credential.py.  We probably have the class
#     relationship upside down, but I haven't refactored this yet.
#     As written, this is really a test of FileBackedJsonObject,
#     and Credential is just an alias for that.
from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException
from tests.util import tdata_resource_file_path


class TestCredential(unittest.TestCase):

    def test_set_data_asserts_valid(self):
        under_test = Credential(data=None, file_path=None)
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.set_data(None)

        under_test.set_data({})

    def test_load(self):
        under_test = Credential(data=None, file_path=None)

        # Load fails where there is no file
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.load()

        # Load works when we have a valid file
        under_test.set_path(
            tdata_resource_file_path('keys/base_test_credential.json'))
        under_test.load()
        self.assertEqual({'test_key': 'test_value'}, under_test.data())

        # A subsequent failed load should throw, but leave the data unchanged.
        under_test.set_path(
            tdata_resource_file_path('keys/FILE_DOES_NOT_EXIST.json'))
        with self.assertRaises(FileNotFoundError):
            # let underlying exception pass to the application
            under_test.load()

        self.assertEqual({'test_key': 'test_value'}, under_test.data())

    def test_lazy_load(self):
        # If data is not set, it should be loaded from the path, but not until
        # the data is requested.
        under_test = Credential(data=None,
                                file_path=tdata_resource_file_path(
                                    'keys/base_test_credential.json'))
        self.assertIsNone(under_test.data())
        under_test.lazy_load()
        self.assertEqual({'test_key': 'test_value'}, under_test.data())

        # if the path is invalid, it should error.
        under_test = Credential(data=None,
                                file_path=tdata_resource_file_path(
                                    'keys/FILE_DOES_NOT_EXIST.json'))
        with self.assertRaises(FileNotFoundError):
            under_test.lazy_load()

        under_test = Credential(data=None, file_path=None)
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.lazy_load()

        # Should be fine if data is set, and a lazy_load() is tried with no
        # path set or an invalid path set, no load should be performed and the
        # data should be unchanged.
        under_test = Credential(data={'ctor_key': 'ctor_value'},
                                file_path=None)
        under_test.lazy_load()
        self.assertEqual({'ctor_key': 'ctor_value'}, under_test.data())

        under_test = Credential(data={'ctor_key': 'ctor_value'},
                                file_path=tdata_resource_file_path(
                                    'keys/base_test_credential.json'))
        under_test.lazy_load()
        self.assertEqual({'ctor_key': 'ctor_value'}, under_test.data())

        under_test = Credential(data={'ctor_key': 'ctor_value'},
                                file_path=tdata_resource_file_path(
                                    'keys/FILE_DOES_NOT_EXIST.json'))
        under_test.lazy_load()
        self.assertEqual({'ctor_key': 'ctor_value'}, under_test.data())

    def test_lazy_reload_initial_load_behavior(self):
        # Behaves like lazy load when there is no data:
        # If data is not set, it should be loaded from the path, but not until
        # the data is asked for.
        under_test = Credential(data=None,
                                file_path=tdata_resource_file_path(
                                    'keys/base_test_credential.json'))
        self.assertIsNone(under_test.data())
        under_test.lazy_reload()
        self.assertEqual({'test_key': 'test_value'}, under_test.data())

        # if the path is invalid, it should error.
        under_test = Credential(data=None,
                                file_path=tdata_resource_file_path(
                                    'keys/FILE_DOES_NOT_EXIST.json'))
        with self.assertRaises(FileNotFoundError):
            under_test.lazy_reload()

        under_test = Credential(data=None, file_path=None)
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.lazy_reload()

        # Behaves like lazy_load when there is data but no file - contiues
        # with in memory data
        under_test = Credential(data={'ctor_key': 'ctor_value'},
                                file_path=None)
        under_test.lazy_reload()
        self.assertEqual({'ctor_key': 'ctor_value'}, under_test.data())

        # But, if the file is set, problems with the file are an error, which
        # differs from lazy_load()
        under_test = Credential(data={'ctor_key': 'ctor_value'},
                                file_path=tdata_resource_file_path(
                                    'keys/FILE_DOES_NOT_EXIST.json'))
        with self.assertRaises(FileNotFoundError):
            under_test.lazy_reload()

    def test_lazy_reload_reload_behavior(self):
        tmp_dir = tempfile.TemporaryDirectory()
        test_path = pathlib.Path(tmp_dir.name) / 'lazy_reload_test.json'
        shutil.copyfile(
            tdata_resource_file_path('keys/base_test_credential.json'),
            test_path)

        under_test = Credential(data=None, file_path=None)

        # test that it doesn't load until asked for
        under_test.set_path(test_path)
        self.assertIsNone(under_test.data())
        test_key_value = under_test.lazy_get('test_key')
        self.assertEqual('test_value', test_key_value)

        # test that changing the file DOES trigger a reload.
        new_test_data = copy.deepcopy(under_test.data())
        new_test_data['test_key'] = 'new_data'
        new_credential = Credential(data=new_test_data, file_path=test_path)
        time.sleep(2)
        new_credential.save()

        under_test.lazy_reload()
        test_key_value = under_test.lazy_get('test_key')
        self.assertEqual('new_data', test_key_value)

        # a subsequent reload when the file has not been modified should
        # NOT trigger a reload. (peek at the internals to check.)
        old_load_time = under_test._load_time
        time.sleep(2)
        under_test.lazy_reload()
        new_load_time = under_test._load_time
        self.assertEqual(old_load_time, new_load_time)

    def test_save(self):
        tmp_dir = tempfile.TemporaryDirectory()
        test_path = pathlib.Path(tmp_dir.name) / 'save_test.json'
        test_data = {'some_key': 'some_data'}

        # invalid data refuses to save
        under_test = Credential(data=None, file_path=test_path)
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.save()

        # Path must be set
        under_test = Credential(data=test_data, file_path=None)
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.save()

        # Validate data saved correctly, and can be reconstituted in an
        # equivalent credential object.
        under_test = Credential(data=test_data, file_path=test_path)
        under_test.save()
        test_reader = Credential(data=None, file_path=test_path)
        test_reader.load()
        self.assertEqual(test_data, test_reader.data())

    def test_getters_setters(self):
        test_path = pathlib.Path('/test/test_credential.json')
        test_data = {'some_key': 'some_data'}

        under_test = Credential(data=None, file_path=None)
        self.assertIsNone(under_test.data())
        self.assertIsNone(under_test.path())
        under_test.set_path(test_path)
        under_test.set_data(test_data)
        self.assertEqual(test_data, under_test.data())
        self.assertEqual(test_path, under_test.path())
