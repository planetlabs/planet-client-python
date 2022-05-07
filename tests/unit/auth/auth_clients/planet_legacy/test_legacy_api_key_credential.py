import unittest

from planet.auth.planet_legacy.legacy_api_key import \
    FileBackedPlanetLegacyAPIKey
from planet.auth.util import FileBackedJsonObjectException
from tests.util import tdata_resource_file_path


class TestLegacyCredential(unittest.TestCase):

    def test_asserts_valid(self):
        under_test = FileBackedPlanetLegacyAPIKey(
            api_key=None,
            api_key_file=tdata_resource_file_path(
                'keys/planet_legacy_test_credential.json'))
        under_test.load()
        self.assertEqual('test_legacy_api_key', under_test.legacy_api_key())

        with self.assertRaises(FileBackedJsonObjectException):
            under_test.set_data(None)

        with self.assertRaises(FileBackedJsonObjectException):
            under_test.set_data({'test': 'missing required fields'})

    def test_construct_with_literal(self):
        under_test = FileBackedPlanetLegacyAPIKey(
            api_key='test_literal_apikey')
        self.assertEqual('test_literal_apikey', under_test.legacy_api_key())

    def test_getters(self):
        under_test = FileBackedPlanetLegacyAPIKey(
            api_key=None,
            api_key_file=tdata_resource_file_path(
                'keys/planet_legacy_test_credential.json'))
        under_test.load()
        self.assertEqual('test_legacy_api_key', under_test.legacy_api_key())
