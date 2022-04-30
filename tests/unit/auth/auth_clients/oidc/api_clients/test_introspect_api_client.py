import json
import unittest

from requests.auth import AuthBase
from requests.models import Response
from typing import Tuple, Optional
from unittest import mock

from planet.auth.oidc.api_clients.introspect_api_client import \
    IntrospectionAPIClient, IntrospectionAPIException

TEST_API_ENDPOINT = "http://blackhole.unittest.planet.com/introspect"
TEST_ACCESS_TOKEN = "__test_access_token__"
TEST_ID_TOKEN = "__test_id_token__"
TEST_REFRESH_TOKEN = "__test_refresh_token__"
INTROSPECTION_RESPONSE_VALID = {
    'active': True,
    'scope': 'offline_access profile openid',
    'username': 'mock_test_user@planet.com',
    'exp': 1651255371,
    'iat': 1651251771,
    'sub': 'mock_test_user@planet.com',
    'aud': 'https://api.planet.com/mock_audience',
    'iss': 'https://account.planet.com/mock_issuer',
    'jti': 'mock_token_id',
    'token_type': 'Bearer',
    'client_id': 'mock_client_id',
    'uid': 'mock_user_id',
    'api_key': 'PLAK_MyKey',
    'user_id': 123456,
    'organization_id': 1,
    'role_level': 100
}
INTROSPECTION_RESPONSE_FAILED = {'active': False}


def noop_auth_enricher(raw_payload: dict,
                       audience: str) -> Tuple[dict, Optional[AuthBase]]:
    return raw_payload, None


def mocked_validate_ok(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps(INTROSPECTION_RESPONSE_VALID))
    return response


def mocked_validate_fail(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps(INTROSPECTION_RESPONSE_FAILED))
    return response


class IntrospectApiClientTest(unittest.TestCase):

    @mock.patch('requests.post', side_effect=mocked_validate_ok)
    def test_validate_access_token_valid_with_enricher(self, mock_post):
        under_test = IntrospectionAPIClient(introspect_uri=TEST_API_ENDPOINT)
        validation_data = under_test.validate_access_token(
            TEST_ACCESS_TOKEN, noop_auth_enricher)
        self.assertEqual(INTROSPECTION_RESPONSE_VALID, validation_data)

    @mock.patch('requests.post', side_effect=mocked_validate_ok)
    def test_validate_access_token_valid(self, mock_post):
        under_test = IntrospectionAPIClient(introspect_uri=TEST_API_ENDPOINT)
        validation_data = under_test.validate_access_token(
            TEST_ACCESS_TOKEN, None)
        self.assertEqual(INTROSPECTION_RESPONSE_VALID, validation_data)

    @mock.patch('requests.post', side_effect=mocked_validate_fail)
    def test_validate_access_token_expired(self, mock_post):
        under_test = IntrospectionAPIClient(introspect_uri=TEST_API_ENDPOINT)
        with self.assertRaises(IntrospectionAPIException):
            under_test.validate_access_token(TEST_ACCESS_TOKEN, None)

    @mock.patch('requests.post', side_effect=mocked_validate_ok)
    def test_validate_id_token(self, mock_post):
        under_test = IntrospectionAPIClient(introspect_uri=TEST_API_ENDPOINT)
        validation_data = under_test.validate_id_token(TEST_ID_TOKEN, None)
        self.assertEqual(INTROSPECTION_RESPONSE_VALID, validation_data)

    @mock.patch('requests.post', side_effect=mocked_validate_ok)
    def test_validate_refresh_token(self, mock_post):
        under_test = IntrospectionAPIClient(introspect_uri=TEST_API_ENDPOINT)
        validation_data = under_test.validate_refresh_token(
            TEST_REFRESH_TOKEN, None)
        self.assertEqual(INTROSPECTION_RESPONSE_VALID, validation_data)
