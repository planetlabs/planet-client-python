import pathlib
import unittest
from unittest import mock

from planet.auth.auth_client import AuthClientException
from planet.auth.oidc.auth_clients.client_credentials_flow import \
    ClientCredentialsSharedKeyAuthClient, \
    ClientCredentialsSharedKeyClientConfig, \
    ClientCredentialsPubKeyAuthClient, \
    ClientCredentialsPubKeyClientConfig, \
    ClientCredentialsClientSecretAuthClient, \
    ClientCredentialsClientSecretClientConfig
from planet.auth.oidc.oidc_token import FileBackedOidcToken
from planet.auth.oidc.request_authenticator import \
    RefreshOrReloginOidcTokenRequestAuthenticator
from tests.util import tdata_resource_file_path

TEST_AUTH_SERVER = 'https://blackhole.unittest.planet.com/fake_authserver'
TEST_CLIENT_ID = 'fake_test_client_id'
TEST_CLIENT_SECRET = 'fake_test_client_secret'
TEST_TOKEN_SAVE_FILE_PATH = pathlib.Path('/test/token.json')
MOCK_TOKEN = {
    "token_type": "Bearer",
    "expires_in": 3600,
    "access_token": "__mock_access_token__",
    "scope": "planet"
}


def mocked_tokenapi_ccred_client_secret(obj_self,
                                        client_id,
                                        client_secret,
                                        requested_scopes):
    return MOCK_TOKEN


def mocked_tokenapi_ccred_pubkey(obj_self,
                                 client_id,
                                 private_key,
                                 requested_scopes):
    return MOCK_TOKEN


class ClientCredentialsClientSecretFlowTest(unittest.TestCase):

    def setUp(self):
        self.under_test = ClientCredentialsClientSecretAuthClient(
            ClientCredentialsClientSecretClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET))

    @mock.patch(
        'planet.auth.oidc.api_clients.token_api_client.TokenAPIClient.get_token_from_client_credentials_secret',  # noqa
        mocked_tokenapi_ccred_client_secret)
    def test_login(self):
        test_result = self.under_test.login()
        self.assertIsInstance(test_result, FileBackedOidcToken)
        self.assertEqual(MOCK_TOKEN, test_result.data())

        # again with override scopes, but since the response is mocked
        # there is nothing different to check in the result data
        test_result = self.under_test.login(requested_scopes=['override1'])
        self.assertIsInstance(test_result, FileBackedOidcToken)
        # self.assertEqual(MOCK_TOKEN, test_result.data())

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            token_file_path=TEST_TOKEN_SAVE_FILE_PATH)
        self.assertIsInstance(test_result,
                              RefreshOrReloginOidcTokenRequestAuthenticator)

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


def mocked_pem_load_error(key_data, **kwargs):
    return None


class ClientCredentialsPubKeyConfigTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.privkey_password = 'password'
        cls.privkey_file_path = tdata_resource_file_path(
            'keys/keypair1_priv.test_pem')
        with open(cls.privkey_file_path) as key_file:
            cls.privkey_literal_str = key_file.read()

        cls.privkey_file_path_nopassword = tdata_resource_file_path(
            'keys/keypair1_priv_nopassword.test_pem')
        with open(cls.privkey_file_path_nopassword) as key_file:
            cls.privkey_literal_str_nopassword = key_file.read()

    def _assert_rsa_keys_equal(self, key1, key2):
        # We are not validating the crypto libs. We assume if both keys
        # loaded without throwing and look similar, our code is working as
        # expected.
        self.assertEqual(key1.key_size, key2.key_size)

    def test_key_loads_from_literal_or_file(self):
        under_test_literal = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        under_test_filebacked = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        self._assert_rsa_keys_equal(under_test_filebacked.private_key_data(),
                                    under_test_literal.private_key_data())

    def test_key_loads_with_or_without_password_literal(self):
        under_test_nopw = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        under_test_pw = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str,
            client_privkey_password=self.privkey_password)
        key_nopw = under_test_nopw.private_key_data()
        key_pw = under_test_pw.private_key_data()
        self._assert_rsa_keys_equal(key_pw, key_nopw)

    def test_key_loads_with_or_without_password_filebacked(self):
        under_test_nopw = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        under_test_pw = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path,
            client_privkey_password=self.privkey_password)
        key_nopw = under_test_nopw.private_key_data()
        key_pw = under_test_pw.private_key_data()
        self._assert_rsa_keys_equal(key_pw, key_nopw)

    def test_bad_password_throws(self):
        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password=None,
            client_privkey=self.privkey_literal_str)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password='bad password',
            client_privkey=self.privkey_literal_str)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password=None,
            client_privkey_file=self.privkey_file_path)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password='bad password',
            client_privkey_file=self.privkey_file_path)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

    @mock.patch(
        'cryptography.hazmat.primitives.serialization.load_pem_private_key',
        mocked_pem_load_error)  # noqa
    def test_unexpected_keyload_restult(self):
        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

    def test_no_key_configured(self):
        under_test = ClientCredentialsPubKeyClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=None,
            client_privkey_file=None,
            client_privkey_password=None)
        with self.assertRaises(AuthClientException):
            under_test.private_key_data()

    def test_lazy_load_only_once(self):
        # TODO: test that private_key_data() only loads on the first call
        pass


class ClientCredentialsPubKeyFlowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.privkey_password = 'password'
        cls.privkey_file_path = tdata_resource_file_path(
            'keys/keypair1_priv.test_pem')

    def setUp(self):
        self.under_test = ClientCredentialsPubKeyAuthClient(
            ClientCredentialsPubKeyClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                client_id=TEST_CLIENT_ID,
                client_privkey_password=self.privkey_password,
                client_privkey_file=self.privkey_file_path))

    @mock.patch(
        'planet.auth.oidc.api_clients.token_api_client.TokenAPIClient.get_token_from_client_credentials_pubkey',  # noqa
        mocked_tokenapi_ccred_pubkey)
    def test_login(self):
        test_result = self.under_test.login()
        self.assertIsInstance(test_result, FileBackedOidcToken)
        self.assertEqual(MOCK_TOKEN, test_result.data())

        # again with override scopes, but since the response is mocked
        # there is nothing different to check in the result data
        test_result = self.under_test.login(requested_scopes=['override1'])
        self.assertIsInstance(test_result, FileBackedOidcToken)
        # self.assertEqual(MOCK_TOKEN, test_result.data())

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            token_file_path=TEST_TOKEN_SAVE_FILE_PATH)
        self.assertIsInstance(test_result,
                              RefreshOrReloginOidcTokenRequestAuthenticator)

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


class ClientCredentialsSharedKeyFlowTest(unittest.TestCase):

    def setUp(self):
        self.under_test = ClientCredentialsSharedKeyAuthClient(
            ClientCredentialsSharedKeyClientConfig(
                auth_server=TEST_AUTH_SERVER,
                token_endpoint=TEST_AUTH_SERVER + '/token',
                client_id=TEST_CLIENT_ID,
                shared_key=None))

    def test_login(self):
        # Dummy fake test since there is no real implementation yet.
        # this is here just to not let the stub class fail test coverage
        # requirements.
        with self.assertRaises(Exception):
            self.under_test.login()

    def test_default_request_authenticator_type(self):
        test_result = self.under_test.default_request_authenticator(
            token_file_path=TEST_TOKEN_SAVE_FILE_PATH)
        self.assertIsInstance(test_result,
                              RefreshOrReloginOidcTokenRequestAuthenticator)

    def test_auth_enricher(self):
        # Dummy fake test since there is no real implementation yet.
        # this is here just to not let the stub class fail test coverage
        # requirements.
        with self.assertRaises(Exception):
            self.under_test._client_auth_enricher(None, None)
