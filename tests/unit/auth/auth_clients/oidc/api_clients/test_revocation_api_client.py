import json
import unittest

from requests.auth import AuthBase
from requests.models import Response
from typing import Tuple, Optional
from unittest import mock

from planet.auth.oidc.api_clients.revocation_api_client import \
    RevocationApiClient

TEST_API_ENDPOINT = 'https://blackhole.unittest.planet.com/api'
TEST_ACCESS_TOKEN = "__test_access_token__"
TEST_REFRESH_TOKEN = "__test_refresh_token__"
API_RESPONSE_VALID = {}
API_RESPONSE_FAILED = {}


def noop_auth_enricher(raw_payload: dict,
                       audience: str) -> Tuple[dict, Optional[AuthBase]]:
    return raw_payload, None


def mocked_response_ok(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    response.headers['content-type'] = 'application/json'
    response._content = str.encode(json.dumps(API_RESPONSE_VALID))
    return response


class RevocationApiClientTest(unittest.TestCase):
    """
    Revocation API testing is very boring.  By design, the endpoint doesn't
    tell you much. All of our expected error handling is tested with the base
    class.
    """

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_revoke_access_token_with_enricher(self, mock_post):
        under_test = RevocationApiClient(revocation_uri=TEST_API_ENDPOINT)
        under_test.revoke_access_token(TEST_ACCESS_TOKEN, noop_auth_enricher)

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_revoke_access_token_without_enricher(self, mock_post):
        under_test = RevocationApiClient(revocation_uri=TEST_API_ENDPOINT)
        under_test.revoke_access_token(TEST_ACCESS_TOKEN, None)

    @mock.patch('requests.post', side_effect=mocked_response_ok)
    def test_revoke_refresh_token(self, mock_post):
        under_test = RevocationApiClient(revocation_uri=TEST_API_ENDPOINT)
        under_test.revoke_refresh_token(TEST_REFRESH_TOKEN, None)
