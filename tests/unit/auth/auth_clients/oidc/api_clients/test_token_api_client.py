import json
import unittest

from requests.models import Response
from requests.auth import AuthBase
from typing import Tuple, Optional
from unittest import mock

from planet.auth.oidc.api_clients.token_api_client import TokenApiClient, \
    TokenApiException
from planet.auth.oidc.util import create_pkce_challenge_verifier_pair

TEST_API_ENDPOINT = 'https://blackhole.unittest.planet.com/api'
TEST_CLIENT_ID = '__test_client_id__'
TEST_REDIRECT_URI = '__test_redirect_uri__'
TEST_ACCESS_TOKEN = "__test_access_token__"
TEST_ID_TOKEN = "__test_id_token__"
TEST_REFRESH_TOKEN = "__test_refresh_token__"
API_RESPONSE_VALID = {
    "token_type": "Bearer",
    "expires_in": 3600,
    "access_token": "_dummy_access_token_",
    "scope": "offline_access profile openid",
    "refresh_token": "_dummy_refresh_token_",
    "id_token": "_dummy_id_token_"
}
API_RESPONSE_INVALID = {  # it looks valid, but no "expires_in"
    "token_type": "Bearer",
    "access_token": "_dummy_access_token_",
    "scope": "offline_access profile openid",
    "refresh_token": "_dummy_refresh_token_",
    "id_token": "_dummy_id_token_"
}


def mocked_response_ok(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps(API_RESPONSE_VALID))
    return response


def mocked_response_invalid(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps(API_RESPONSE_INVALID))
    return response


# def load_privkey():
#     return load_rsa_private_key(
#         tdata_resource_file_path('keys/keypair1_priv.test_pem'), 'password')


class TokenApiClientTest(unittest.TestCase):

    def _test_auth_enricher(self, raw_payload: dict,
                            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        return raw_payload, None

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_token_from_authcode_valid(self, mock_post):
        under_test = TokenApiClient(token_uri=TEST_API_ENDPOINT)
        pkce_code_verifier, pkce_code_challenge = \
            create_pkce_challenge_verifier_pair()
        token_response = under_test.get_token_from_code(
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_REDIRECT_URI,
            code='dummy_authcode',
            code_verifier=pkce_code_verifier)
        self.assertEqual(API_RESPONSE_VALID, token_response)

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_token_from_authcode_valid_with_auth_enricher(self, mock_post):
        under_test = TokenApiClient(token_uri=TEST_API_ENDPOINT)
        pkce_code_verifier, pkce_code_challenge = \
            create_pkce_challenge_verifier_pair()
        token_response = under_test.get_token_from_code(
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_REDIRECT_URI,
            code='dummy_authcode',
            code_verifier=pkce_code_verifier,
            auth_enricher=self._test_auth_enricher)
        self.assertEqual(API_RESPONSE_VALID, token_response)

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_token_from_client_credentials(self, mock_post):
        under_test = TokenApiClient(token_uri=TEST_API_ENDPOINT)
        # private_key = load_privkey()
        token_response = under_test.get_token_from_client_credentials(
            TEST_CLIENT_ID)
        self.assertEqual(API_RESPONSE_VALID, token_response)
        # Coverage complains when we don't test the custom scopes
        # branch, but the server and it's response is mock, so we
        # don't actually have anything different to check in the result.
        # All we can check is that it didn't throw.
        under_test.get_token_from_client_credentials(
            TEST_CLIENT_ID, requested_scopes=['scope1', 'scope2'])

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_token_from_refresh_valid(self, mock_post):
        under_test = TokenApiClient(token_uri=TEST_API_ENDPOINT)
        token_response = under_test.get_token_from_refresh(
            TEST_CLIENT_ID, TEST_REFRESH_TOKEN)
        self.assertEqual(API_RESPONSE_VALID, token_response)
        # Coverage complains when we don't test the custom scopes
        # branch, but the server and it's response is mock, so we
        # don't actually have anything different to check in the result.
        # All we can check is that it didn't throw.
        token_response = under_test.get_token_from_refresh(
            TEST_CLIENT_ID,
            TEST_REFRESH_TOKEN,
            requested_scopes=['scope1', 'scope2'])

    @mock.patch('requests.post', side_effect=mocked_response_invalid)
    def test_invalid_response(self, mock_post):
        under_test = TokenApiClient(token_uri=TEST_API_ENDPOINT)
        pkce_code_verifier, pkce_code_challenge = \
            create_pkce_challenge_verifier_pair()
        with self.assertRaises(TokenApiException):
            under_test.get_token_from_code(TEST_CLIENT_ID,
                                           TEST_REDIRECT_URI,
                                           'dummy_authcode',
                                           pkce_code_verifier)
