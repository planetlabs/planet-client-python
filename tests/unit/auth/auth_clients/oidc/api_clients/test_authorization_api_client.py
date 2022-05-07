import http.server
import logging
import urllib.parse

import requests
import unittest

from requests.auth import AuthBase
from typing import Tuple, Optional
from unittest import mock
from urllib.parse import urlparse, parse_qs

from planet.auth.oidc.api_clients.authorization_api_client import \
    AuthorizationAPIClient, AuthorizationAPIException, \
    _parse_authcode_from_callback
from planet.auth.oidc.util import create_pkce_challenge_verifier_pair
from tests.util import background, find_free_port

TEST_API_ENDPOINT = 'https://blackhole.unittest.planet.com/api'
TEST_CLIENT_ID = '_client_id_'
TEST_REDIRECT_URI_TEMPLATE = 'http://localhost:{}/utest_callback_uri'
TEST_REQUESTED_SCOPES = ['scope1', 'scope2']
MOCK_AUTHCODE = '_mock_authcode_'
API_RESPONSE_VALID = {}
API_RESPONSE_FAILED = {}
TEST_VERIFIER, TEST_CHALLENGE = create_pkce_challenge_verifier_pair()

logger = logging.getLogger(__name__)


def noop_auth_enricher(raw_payload: dict,
                       audience: str) -> Tuple[dict, Optional[AuthBase]]:
    return raw_payload, None


def mocked_get_password(**kwargs):
    return MOCK_AUTHCODE


def mocked_generate_nonce(length):
    # Need to defeat the cryptographic nonce for some tests.
    nonce_charset = '1234567890abcdefghijklmnopqrstuvwxyz'
    return ''.join([str(nonce_charset[i % 36]) for i in range(length)])


@background
def fire_and_forget_http_get(url):
    requests.get(url)


def mocked_browser_authserver(request_url, arg2, **kwargs):
    # TODO: assert it's constructed the way we want? The only real
    #       branching in the code under test is handling of scopes
    #       At some point, validating this URL is partially implementing
    #       an authorization server
    parsed_query_string = parse_qs(urlparse(request_url).query)
    redirect_uri = parsed_query_string.get('redirect_uri')[0]
    state = parsed_query_string.get('state')[0]
    encoded_params = urllib.parse.urlencode({
        'state': state, 'code': MOCK_AUTHCODE
    })
    callback_uri = '{}?{}'.format(redirect_uri, encoded_params)

    # I don't care about the result, so run in the background and forget.
    # Against a live auth service, this callback would be called by the
    # browser after an exchange with th auth server and a final redirect.
    # Mocking the browser mocks the auth server interaction
    fire_and_forget_http_get(callback_uri)


class CallbackHandlerTest(unittest.TestCase):
    # There is really no branching logic in this class other than a logging
    # handler. It's purpose in life is to recapture the flow from the browser
    # and save that data for all the other code, which should already have
    # test coverage elsewhere.
    pass


class AuthcodeCallbackParserTest(unittest.TestCase):

    def setUp(self):
        self.under_test = _parse_authcode_from_callback
        self.dummy_callback_baseurl = TEST_REDIRECT_URI_TEMPLATE.format(8080)

    def test_empty_request_throws(self):
        with self.assertRaises(AuthorizationAPIException):
            self.under_test(None, None)

        with self.assertRaises(AuthorizationAPIException):
            self.under_test('', None)

    def test_explicit_error_throws(self):
        encoded_params = urllib.parse.urlencode({'error': 'test_error_1'})
        callback_uri = '{}?{}'.format(self.dummy_callback_baseurl,
                                      encoded_params)
        with self.assertRaises(AuthorizationAPIException):
            self.under_test(callback_uri, None)

        # Mix it up. We want a failure whenever there is an error, even if
        # there is also an auth code (this really shouldn't ever happen).
        encoded_params = urllib.parse.urlencode({
            'error':
            'test_error_2',
            'error_description':
            'test error description',
            'code':
            MOCK_AUTHCODE,
            'state':
            mocked_generate_nonce(8)
        })
        callback_uri = '{}?{}'.format(self.dummy_callback_baseurl,
                                      encoded_params)
        with self.assertRaises(AuthorizationAPIException):
            self.under_test(callback_uri, None)

    # @mock.patch('planet.auth.oidc.util.generate_nonce', mocked_generate_nonce)  # noqa
    def test_state_is_checked(self):
        test_state_1 = mocked_generate_nonce(8)
        test_state_2 = test_state_1 + '_STATE_IS_CORRUPTED'

        encoded_params = urllib.parse.urlencode({
            'code': MOCK_AUTHCODE, 'state': test_state_1
        })
        callback_uri = '{}?{}'.format(self.dummy_callback_baseurl,
                                      encoded_params)
        auth_code = self.under_test(callback_uri, test_state_1)
        self.assertEqual(MOCK_AUTHCODE, auth_code)

        encoded_params = urllib.parse.urlencode({
            'code': MOCK_AUTHCODE, 'state': test_state_2
        })
        callback_uri = '{}?{}'.format(self.dummy_callback_baseurl,
                                      encoded_params)
        with self.assertRaises(AuthorizationAPIException):
            self.under_test(callback_uri, test_state_1)

    def test_callback_not_understood_throws(self):
        encoded_params = urllib.parse.urlencode({'data1': 'some random data'})
        callback_uri = '{}?{}'.format(self.dummy_callback_baseurl,
                                      encoded_params)
        with self.assertRaises(AuthorizationAPIException):
            self.under_test(callback_uri, None)


class AuthorizationApiClientTest(unittest.TestCase):

    def setUp(self):
        self.callback_port = find_free_port()
        self.callback_uri = TEST_REDIRECT_URI_TEMPLATE.format(
            self.callback_port)
        self.pkce_verifier, self.pkce_challenge = create_pkce_challenge_verifier_pair() # noqa

    @mock.patch('webbrowser.open', mocked_browser_authserver)
    def test_get_authcode_with_browser_and_listener(self):
        under_test = AuthorizationAPIClient(
            authorization_uri=TEST_API_ENDPOINT)

        # Cover both default and override scope paths
        # TODO: a better test would be to catch the URL that is constructed
        #       and verify it.  A real verification of that URL amounts to
        #       implementing a partial authorization server.
        authcode = under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
            TEST_CLIENT_ID,
            self.callback_uri,
            None,
            self.pkce_challenge)
        self.assertEqual(MOCK_AUTHCODE, authcode)

        authcode = under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
            TEST_CLIENT_ID,
            self.callback_uri,
            TEST_REQUESTED_SCOPES,
            self.pkce_challenge)
        self.assertEqual(MOCK_AUTHCODE, authcode)

    @mock.patch('http.server.HTTPServer')
    @mock.patch(
        'planet.auth.oidc.api_clients.authorization_api_client._parse_authcode_from_callback'  # noqa
    )
    @mock.patch('webbrowser.open')
    def test_get_authcode_with_browser_and_listener_unsupported_callback_host(
            self, mock1, mock2, mock3):
        under_test = AuthorizationAPIClient(
            authorization_uri=TEST_API_ENDPOINT)

        # Only localhost callbacks should be supported by current code
        valid_callback_1 = 'http://localhost:{}/test'.format(
            self.callback_port)
        valid_callback_2 = 'http://127.0.0.1:{}/test'.format(
            self.callback_port)
        invalid_callback = 'https://test.planet.com:443'

        under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
            TEST_CLIENT_ID,
            valid_callback_1,
            None,
            self.pkce_challenge)

        under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
            TEST_CLIENT_ID,
            valid_callback_2,
            None,
            self.pkce_challenge)

        with self.assertRaises(AuthorizationAPIException):
            under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
                TEST_CLIENT_ID,
                invalid_callback,
                None,
                self.pkce_challenge)

    @mock.patch('http.server.HTTPServer', spec=http.server.HTTPServer)
    @mock.patch('webbrowser.open')
    def test_get_authcode_with_browser_and_listener_unknown_callback_failure(
            self, mock1, mock2):
        under_test = AuthorizationAPIClient(
            authorization_uri=TEST_API_ENDPOINT)
        with self.assertRaises(AuthorizationAPIException):
            under_test.authcode_from_pkce_flow_with_browser_with_callback_listener(  # noqa
                TEST_CLIENT_ID,
                self.callback_uri,
                None,
                self.pkce_challenge)

    @mock.patch('getpass.getpass', mocked_get_password)
    def test_get_authcode_without_browser_and_listener(self):
        under_test = AuthorizationAPIClient(
            authorization_uri=TEST_API_ENDPOINT)

        # Cover both default and override scope paths
        # TODO: a better test would be to catch the URL that is constructed
        #       and verify it.  A real verification of that URL amounts to
        #       implementing a partial authorization server.
        authcode = under_test.authcode_from_pkce_flow_without_browser_without_callback_listener(  # noqa
            TEST_CLIENT_ID,
            self.callback_uri,
            None,
            self.pkce_challenge)
        self.assertEqual(MOCK_AUTHCODE, authcode)

        authcode = under_test.authcode_from_pkce_flow_without_browser_without_callback_listener(  # noqa
            TEST_CLIENT_ID,
            self.callback_uri,
            TEST_REQUESTED_SCOPES,
            self.pkce_challenge)
        self.assertEqual(MOCK_AUTHCODE, authcode)
