import unittest

from planet.auth.static_api_key.request_authenticator import \
    FileBackedAPIKeyRequestAuthenticator
from planet.auth.static_api_key.static_api_key import FileBackedAPIKey
from planet.auth.util import FileBackedJsonObjectException
from tests.util import tdata_resource_file_path


class StaticApiKeyRequestAuthenticatorTest(unittest.TestCase):

    def test_pre_request_hook_loads_from_file_happy_path(self):
        under_test = FileBackedAPIKeyRequestAuthenticator(
            auth_file=FileBackedAPIKey(api_key_file=tdata_resource_file_path(
                'keys/static_api_key_test_credential.json')))
        under_test.pre_request_hook()
        self.assertEqual('test_api_key', under_test._token_body)
        self.assertEqual('test_prefix', under_test._token_prefix)

    def test_pre_request_hook_loads_from_file_invalid_throws(self):
        under_test = FileBackedAPIKeyRequestAuthenticator(
            auth_file=FileBackedAPIKey(api_key_file=tdata_resource_file_path(
                'keys/invalid_test_credential.json')))
        with self.assertRaises(FileBackedJsonObjectException):
            under_test.pre_request_hook()
