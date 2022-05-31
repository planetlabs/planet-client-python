import pathlib
import unittest
from unittest import mock

from planet.auth.auth_client import AuthClientConfigException
from planet.auth.oidc.auth_clients.auth_code_flow import \
    AuthCodePKCEAuthClient, \
    AuthCodePKCEClientConfig, \
    AuthCodePKCEWithClientSecretAuthClient, \
    AuthCodePKCEWithClientSecretClientConfig, \
    AuthCodePKCEWithPubKeyAuthClient, \
    AuthCodePKCEWithPubKeyClientConfig
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.oidc.request_authenticator import \
    RefreshingOidcTokenRequestAuthenticator
from tests.util import tdata_resource_file_path

TEST_AUTH_SERVER = 'https://blackhole.unittest.planet.com/fake_authserver'
TEST_CLIENT_ID = 'fake_test_client_id'
TEST_CLIENT_SECRET = 'fake_client_secret'
TEST_RECIRECT_URI_REMOTE = \
    'https://blackhole.unittest.planet.com/auth_callback'
TEST_RECIRECT_URI_LOCAL = 'http://localhost:8080/auth_callback'
TEST_TOKEN_SAVE_FILE_PATH = pathlib.Path('/test/token.json')
TEST_AUTH_CODE = 'FAKE_TEST_AUTHCODE'
MOCK_TOKEN = {
    "token_type": "Bearer",
    "expires_in": 3600,
    "access_token": "__mock_access_token__",
    "scope": "offline_access openid profile planet",
    "refresh_token": "__mock_refresh_token__",
    "id_token": "__mock_id_token__"
}


class AuthCodePKCEClientConfigTest(unittest.TestCase):

    def test_callback_urls_set(self):
        under_test = AuthCodePKCEClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_RECIRECT_URI_REMOTE,
            local_redirect_uri=TEST_RECIRECT_URI_LOCAL)
        self.assertEqual(TEST_RECIRECT_URI_REMOTE, under_test.redirect_uri)
        self.assertEqual(TEST_RECIRECT_URI_LOCAL,
                         under_test.local_redirect_uri)

        under_test = AuthCodePKCEClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_RECIRECT_URI_REMOTE,
            local_redirect_uri=None)
        self.assertEqual(TEST_RECIRECT_URI_REMOTE, under_test.redirect_uri)
        self.assertEqual(TEST_RECIRECT_URI_REMOTE,
                         under_test.local_redirect_uri)

        under_test = AuthCodePKCEClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=None,
            local_redirect_uri=TEST_RECIRECT_URI_LOCAL)
        self.assertEqual(TEST_RECIRECT_URI_LOCAL, under_test.redirect_uri)
        self.assertEqual(TEST_RECIRECT_URI_LOCAL,
                         under_test.local_redirect_uri)

        with self.assertRaises(AuthClientConfigException):
            under_test = AuthCodePKCEClientConfig(auth_server=TEST_AUTH_SERVER,
                                                  client_id=TEST_CLIENT_ID,
                                                  redirect_uri=None,
                                                  local_redirect_uri=None)


def mocked_authapi_get_authcode(obj_self,
                                client_id,
                                redirect_uri,
                                requested_scopes,
                                requested_audiences,
                                pkce_code_challenge):
    return TEST_AUTH_CODE


def mocked_tokenapi_token_from_code(obj_self,
                                    redirect_uri,
                                    client_id,
                                    code,
                                    code_verifier,
                                    auth_enricher):
    return MOCK_TOKEN


class PkceAuthCodeFlowTest(unittest.TestCase):

    def setUp(self):
        self.under_test = AuthCodePKCEAuthClient(
            AuthCodePKCEClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                authorization_endpoint=TEST_AUTH_SERVER + '/auth',
                client_id=TEST_CLIENT_ID,
                redirect_uri=TEST_RECIRECT_URI_LOCAL))

    @mock.patch(
        'planet.auth.oidc.api_clients.authorization_api_client.AuthorizationApiClient.authcode_from_pkce_flow_with_browser_with_callback_listener',  # noqa
        mocked_authapi_get_authcode)
    @mock.patch(
        'planet.auth.oidc.api_clients.token_api_client.TokenApiClient.get_token_from_code',  # noqa
        mocked_tokenapi_token_from_code)
    def test_login_browser(self):
        test_result = self.under_test.login(allow_open_browser=True)
        self.assertIsInstance(test_result, FileBackedOidcCredential)
        self.assertEqual(MOCK_TOKEN, test_result.data())

    @mock.patch(
        'planet.auth.oidc.api_clients.authorization_api_client.AuthorizationApiClient.authcode_from_pkce_flow_without_browser_without_callback_listener',  # noqa
        mocked_authapi_get_authcode)
    @mock.patch(
        'planet.auth.oidc.api_clients.token_api_client.TokenApiClient.get_token_from_code',  # noqa
        mocked_tokenapi_token_from_code)
    def test_login_no_browser(self):
        # override scopes to also test that code path in contrast to the
        # "with browser" case above.
        # No difference in the result between over riding the scopes or not
        # in this test. This is because the response is mocked.  A real auth
        # server might behave differently, but that's beyond the unit under
        # test here.  Same for audiences.
        test_result = self.under_test.login(allow_open_browser=False,
                                            requested_scopes=['override'],
                                            requested_audiences=['req_aud'])
        self.assertIsInstance(test_result, FileBackedOidcCredential)
        self.assertEqual(MOCK_TOKEN, test_result.data())

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            credential_file_path=TEST_TOKEN_SAVE_FILE_PATH)
        self.assertIsInstance(test_result,
                              RefreshingOidcTokenRequestAuthenticator)

    def test_auth_enricher(self):
        # The correctness of what enrichment does is determined by the token
        # endpoint, and we've externalized the heavy lifting of preparing the
        # enrichment into helper functions that could be unit tested
        # separately. (So unit testing of that ought to be done there,
        # although perhaps testing it here in the context of a particular
        # flow here is more meaningful.)
        enriched_payload, auth = self.under_test._client_auth_enricher(
            {}, 'test_audience')

        # Payload enriched with *only* the client id.
        self.assertEqual({'client_id': TEST_CLIENT_ID}, enriched_payload)

        # No request auth expected
        self.assertIsNone(auth)


class AuthCodePKCEWithClientSecretClientConfigTest(unittest.TestCase):

    def test_secret_required(self):
        # No exception
        AuthCodePKCEWithClientSecretClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_RECIRECT_URI_REMOTE,
            client_secret=TEST_CLIENT_SECRET)

        with self.assertRaises(AuthClientConfigException):
            AuthCodePKCEWithClientSecretClientConfig(
                auth_server=TEST_AUTH_SERVER,
                redirect_uri=TEST_RECIRECT_URI_REMOTE,
                client_id=TEST_CLIENT_ID)


class PkceAuthCodeWithSecretFlowTest(unittest.TestCase):

    def setUp(self):
        self.under_test = AuthCodePKCEWithClientSecretAuthClient(
            AuthCodePKCEWithClientSecretClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                authorization_endpoint=TEST_AUTH_SERVER + '/auth',
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET,
                redirect_uri=TEST_RECIRECT_URI_LOCAL))

    def test_auth_enricher(self):
        # The correctness of what enrichment does is determined by the token
        # endpoint, and we've externalized the heavy lifting of preparing the
        # enrichment into helper functions that could be unit tested
        # separately. (So unit testing of that ought to be done there,
        # although perhaps testing it here in the context of a particular
        # flow here is more meaningful.)
        enriched_payload, auth = self.under_test._client_auth_enricher(
            {}, 'test_audience')

        # No payload enrichment expected.
        self.assertEqual({}, enriched_payload)

        # HTTP basic auth with the client secret.
        self.assertEqual(TEST_CLIENT_ID, auth.username)
        self.assertEqual(TEST_CLIENT_SECRET, auth.password)


class AuthCodePKCEWithPubKeyClientConfigTest(unittest.TestCase):

    def test_privkey_required(self):
        # No exception
        AuthCodePKCEWithPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_RECIRECT_URI_REMOTE,
            client_privkey_file='/dummy/utest/file')

        # No exception
        AuthCodePKCEWithPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            redirect_uri=TEST_RECIRECT_URI_REMOTE,
            client_privkey='dummy private key literal')

        with self.assertRaises(AuthClientConfigException):
            AuthCodePKCEWithPubKeyClientConfig(
                auth_server=TEST_AUTH_SERVER,
                redirect_uri=TEST_RECIRECT_URI_REMOTE,
                client_id=TEST_CLIENT_ID)


class PkceAuthCodeWithPubKeyFlowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.privkey_password = 'password'
        cls.privkey_file_path = tdata_resource_file_path(
            'keys/keypair1_priv.test_pem')

    def setUp(self):
        self.under_test = AuthCodePKCEWithPubKeyAuthClient(
            AuthCodePKCEWithPubKeyClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                authorization_endpoint=TEST_AUTH_SERVER + '/auth',
                client_id=TEST_CLIENT_ID,
                client_privkey_password=self.privkey_password,
                client_privkey_file=self.privkey_file_path,
                redirect_uri=TEST_RECIRECT_URI_LOCAL))

    def test_auth_enricher(self):
        # The correctness of what enrichment does is determined by the token
        # endpoint, and we've externalized the heavy lifting of preparing the
        # enrichment into helper functions that could be unit tested
        # separately. (So unit testing of that ought to be done there,
        # although perhaps testing it here in the context of a particular
        # flow here is more meaningful.)
        enriched_payload, auth = self.under_test._client_auth_enricher(
            {}, 'test_audience')

        # Payload enriched with a signed key assertion
        self.assertEqual(
            'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            enriched_payload.get('client_assertion_type'))
        self.assertIsNotNone(enriched_payload.get('client_assertion'))

        # No request auth expected
        self.assertIsNone(auth)
