import http.server
import httpx
import json
import pytest
import requests
import unittest

from planet.auth.request_authenticator import \
    SimpleInMemoryRequestAuthenticator
from tests.util import background, find_free_port, is_cicd

TEST_HEADER = 'x-test-header'
TEST_PREFIX = 'TEST'
TEST_TOKEN = '_test_bearer_token_'
TEST_TIMEOUT = 30


class _UnitTestRequestHandler(http.server.BaseHTTPRequestHandler):

    def __init__(self, request, address, server):
        super().__init__(request, address, server)

    def do_GET(self):
        # Reflect the auth info back so unit test can check it.
        self.send_response(http.HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.server.callback_raw_request_path = self.path
        response_payload = {
            'header_present': bool(self.headers.get(TEST_HEADER)),
            'header_value': self.headers.get(TEST_HEADER)
        }
        self.wfile.write(bytes(json.dumps(response_payload), 'utf-8'))


@background
def handle_test_request_background(listen_port):
    http_server = http.server.HTTPServer(
        ('localhost', listen_port),
        lambda request,
        address,
        server: _UnitTestRequestHandler(request, address, server))
    http_server.timeout = TEST_TIMEOUT
    http_server.handle_request()


@pytest.mark.skipif(
    condition=is_cicd(),
    reason='Skipping tests that listen on a network port for CI/CD')
class RequestAuthenticatorTest(unittest.TestCase):

    def setUp(self):
        self.listen_port = find_free_port()
        handle_test_request_background(self.listen_port)
        self.test_server_url = 'http://localhost:{}/test_request_lib'.format(
            self.listen_port)

    def test_requests_auth(self):
        under_test = SimpleInMemoryRequestAuthenticator(
            token_body=TEST_TOKEN,
            token_prefix=TEST_PREFIX,
            auth_header=TEST_HEADER)
        response = requests.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertTrue(response_json.get('header_present'))
        self.assertEqual(TEST_PREFIX + ' ' + TEST_TOKEN,
                         response_json.get('header_value'))

    def test_requests_noauth(self):
        under_test = SimpleInMemoryRequestAuthenticator(token_body=None,
                                                        token_prefix=None,
                                                        auth_header=None)
        response = requests.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertFalse(response_json.get('header_present'))
        self.assertIsNone(response_json.get('header_value'))

    def test_requests_no_prefix(self):
        under_test = SimpleInMemoryRequestAuthenticator(
            token_body=TEST_TOKEN, token_prefix=None, auth_header=TEST_HEADER)
        response = requests.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertTrue(response_json.get('header_present'))
        self.assertEqual(TEST_TOKEN, response_json.get('header_value'))

    def test_httpx_auth(self):
        under_test = SimpleInMemoryRequestAuthenticator(
            token_body=TEST_TOKEN,
            token_prefix=TEST_PREFIX,
            auth_header=TEST_HEADER)
        response = httpx.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertTrue(response_json.get('header_present'))
        self.assertEqual(TEST_PREFIX + ' ' + TEST_TOKEN,
                         response_json.get('header_value'))

    def test_httpx_noauth(self):
        under_test = SimpleInMemoryRequestAuthenticator(token_body=None,
                                                        token_prefix=None,
                                                        auth_header=None)
        response = httpx.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertFalse(response_json.get('header_present'))
        self.assertIsNone(response_json.get('header_value'))

    def test_httpx_no_prefix(self):
        under_test = SimpleInMemoryRequestAuthenticator(
            token_body=TEST_TOKEN, token_prefix=None, auth_header=TEST_HEADER)
        response = httpx.get(self.test_server_url, auth=under_test)
        response_json = response.json()
        self.assertTrue(response_json.get('header_present'))
        self.assertEqual(TEST_TOKEN, response_json.get('header_value'))

    # TODO: add aiohttp support
