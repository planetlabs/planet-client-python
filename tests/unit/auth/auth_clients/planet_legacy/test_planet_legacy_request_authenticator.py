import unittest

from planet.auth.planet_legacy.legacy_api_key import \
    FileBackedPlanetLegacyApiKey
from planet.auth.planet_legacy.request_authenticator import \
    PlanetLegacyRequestAuthenticator
from planet.auth.util import FileBackedJsonObjectException
from tests.util import tdata_resource_file_path


class PlanetLegacyRequestAuthenticatorTest(unittest.TestCase):

    def test_pre_request_hook_loads_from_file_happy_path(self):
        under_test = PlanetLegacyRequestAuthenticator(
            api_key_file=FileBackedPlanetLegacyApiKey(
                api_key_file=tdata_resource_file_path(
                    'keys/planet_legacy_test_credential.json')))
        under_test.pre_request_hook()
        self.assertEqual('test_legacy_api_key',
                         under_test._api_key_file.legacy_api_key())

    def test_pre_request_hook_loads_from_file_invalid_throws(self):
        under_test = PlanetLegacyRequestAuthenticator(
            api_key_file=FileBackedPlanetLegacyApiKey(
                api_key_file=tdata_resource_file_path(
                    'keys/invalid_test_credential.json')))
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.pre_request_hook()
