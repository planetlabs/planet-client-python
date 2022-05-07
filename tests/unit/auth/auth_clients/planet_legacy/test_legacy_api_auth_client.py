import json
import pathlib
import unittest

from requests.models import Response
from unittest import mock

from planet.auth.planet_legacy.auth_client import PlanetLegacyAuthClient, \
    PlanetLegacyAuthClientConfig, PlanetLegacyAuthClientException
from planet.auth.planet_legacy.legacy_api_key import \
    FileBackedPlanetLegacyAPIKey
from planet.auth.planet_legacy.request_authenticator import \
    PlanetLegacyRequestAuthenticator
from tests.unit.auth.util import TestTokenBuilder
from tests.util import load_rsa_signing_key, tdata_resource_file_path

TEST_MOCK_API_KEY = 'PLAK_MockApiKey'
TEST_AUTH_ENDPOINT = 'https://blackhole.unittest.planet.com/legacy_auth'
TEST_BAD_RESPONSE = {"some_key": "some bogus response payload"}

TEST_SIGNING_KEY = load_rsa_signing_key(
    tdata_resource_file_path('keys/keypair1_priv_nopassword.test_pem'))

TOKEN_BUILDER = TestTokenBuilder(
    tdata_resource_file_path('keys/keypair1_priv_nopassword.test_pem'))


def generate_response_struct(token_str):
    response_struct = {"token": token_str}
    return response_struct


def mock_response_valid(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(
        json.dumps(
            generate_response_struct(
                TOKEN_BUILDER.generate_legacy_token(
                    api_key=TEST_MOCK_API_KEY))))
    return response


def mock_response_http_error(request_url, **kwargs):
    response = Response()
    response.status_code = 401
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps({"error": "access denied"}))
    return response


def mock_response_empty_payload(request_url, **kwargs):
    response = Response()
    response.status_code = 202
    return response


def mock_response_bad_content_type(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'text/plain'
    response._content = str.encode("Plain sting response")
    return response


def mock_response_no_token_in_payload(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(
        json.dumps({"foo": "this test payload lacks a token"}))
    return response


def mock_response_bad_token(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(
        json.dumps(
            generate_response_struct(
                TOKEN_BUILDER.generate_legacy_token(api_key=None))))
    return response


def mocked_getpass_password(**kwargs):
    return "mock_getpass_password"


def mocked_input_username(prompt, **kwargs):
    return "mock_input_username"


class TestLegacyApiAuthClient(unittest.TestCase):

    def setUp(self):
        self.under_test = PlanetLegacyAuthClient(
            PlanetLegacyAuthClientConfig(
                legacy_auth_endpoint=TEST_AUTH_ENDPOINT))

    @mock.patch('requests.post', side_effect=mock_response_valid)
    def test_login_success_direct_input(self, mock1):
        test_result = self.under_test.login(username='test_user',
                                            password='test_password')
        self.assertIsInstance(test_result, FileBackedPlanetLegacyAPIKey)
        self.assertEqual(TEST_MOCK_API_KEY, test_result.legacy_api_key())

    @mock.patch('requests.post', side_effect=mock_response_valid)
    @mock.patch('getpass.getpass', mocked_getpass_password)
    @mock.patch('builtins.input', mocked_input_username)
    def test_login_success_user_prompt(self, mock1):
        test_result = self.under_test.login()
        self.assertIsInstance(test_result, FileBackedPlanetLegacyAPIKey)
        self.assertEqual(TEST_MOCK_API_KEY, test_result.legacy_api_key())

    @mock.patch('requests.post', side_effect=mock_response_http_error)
    def test_login_http_error(self, mock1):
        with self.assertRaises(PlanetLegacyAuthClientException):
            self.under_test.login(username='test_user',
                                  password='test_password')

    @mock.patch('requests.post', side_effect=mock_response_empty_payload)
    def test_login_bad_response_no_payload(self, mock1):
        with self.assertRaises(PlanetLegacyAuthClientException):
            self.under_test.login(username='test_user',
                                  password='test_password')

    @mock.patch('requests.post', side_effect=mock_response_bad_content_type)
    def test_login_bad_response_not_json(self, mock1):
        with self.assertRaises(PlanetLegacyAuthClientException):
            self.under_test.login(username='test_user',
                                  password='test_password')

    @mock.patch('requests.post', side_effect=mock_response_no_token_in_payload)
    def test_login_bad_response_no_token(self, mock1):
        with self.assertRaises(PlanetLegacyAuthClientException):
            self.under_test.login(username='test_user',
                                  password='test_password')

    @mock.patch('requests.post', side_effect=mock_response_bad_token)
    def test_login_bad_response_token_lacks_api_key(self, mock1):
        with self.assertRaises(PlanetLegacyAuthClientException):
            self.under_test.login(username='test_user',
                                  password='test_password')

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            token_file_path=pathlib.Path('/test/token.json'))
        self.assertIsInstance(test_result, PlanetLegacyRequestAuthenticator)
