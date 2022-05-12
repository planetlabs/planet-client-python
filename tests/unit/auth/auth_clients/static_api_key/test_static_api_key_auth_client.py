import pathlib
import unittest

from planet.auth.static_api_key.auth_client import StaticApiKeyAuthClient, \
    StaticApiKeyAuthClientConfig
from planet.auth.static_api_key.request_authenticator import \
    FileBackedApiKeyRequestAuthenticator


class TestStaticApiKeyAuthClient(unittest.TestCase):

    def setUp(self):
        self.under_test = StaticApiKeyAuthClient(
            StaticApiKeyAuthClientConfig())

    def test_login(self):
        # It does nothing. So long as it doesn't throw, we pass.
        self.under_test.login()

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            credential_file_path=pathlib.Path('/test/token.json'))
        self.assertIsInstance(test_result,
                              FileBackedApiKeyRequestAuthenticator)
