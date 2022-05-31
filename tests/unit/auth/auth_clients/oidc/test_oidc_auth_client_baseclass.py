import pathlib
import unittest
from typing import Tuple, Optional
from unittest import mock
from unittest.mock import MagicMock

from requests.auth import AuthBase

from planet.auth.auth_client import AuthClientConfigException
from planet.auth.oidc.auth_client import OidcAuthClient, OidcAuthClientConfig
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.request_authenticator import RequestAuthenticator, \
    SimpleInMemoryRequestAuthenticator
from tests.util import tdata_resource_file_path

TEST_CLIENT_ID = "_FAKE_CLIENT_ID_"
TEST_ACCESS_TOKEN = "_FAKE_ACCESS_TOKEN_"
TEST_TOKEN_FILE = "/test/token.json"
TEST_FAKE_TOKEN_FILE_DATA = {
    "token_type": "Bearer",
    "expires_in": 3600,
    "access_token": "_dummy_access_token_",
    "scope": "offline_access profile openid",
    "refresh_token": "_dummy_refresh_token_",
    "id_token": "_dummy_id_token_"
}

TEST_AUTH_SERVER = 'https://blackhole.unittest.planet.com/fake_authserver'
TEST_DISCOVERED_AUTH_SERVER_BASE = "https://auth.unittest.planet.com"
TEST_OVERRIDE_AUTH_SERVER_BASE = "https://auth_override.unittest.planet.com"
TEST_FAKE_OIDC_DISCOVERY = {
    "issuer":
    TEST_DISCOVERED_AUTH_SERVER_BASE,
    "authorization_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/authorize",
    "token_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/token",
    "userinfo_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/userinfo",
    "registration_endpoint":
    "https://account.planet.com/oauth2/clients",
    "jwks_uri":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/jwks",
    "response_types_supported": [
        "code",
        "id_token",
        "code id_token",
        "code token",
        "id_token token",
        "code id_token token"
    ],
    "response_modes_supported":
    ["query", "fragment", "form_post", "okta_post_message"],
    "grant_types_supported": [
        "authorization_code",
        "implicit",
        "refresh_token",
        "password",
        "urn:ietf:params:oauth:grant-type:device_code"
    ],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": [
        "openid",
        "profile",
        "email",
        "address",
        "phone",
        "offline_access",
        "device_sso"
    ],
    "token_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none"
    ],
    "claims_supported": [
        "iss",
        "ver",
        "sub",
        "aud",
        "iat",
        "exp",
        "jti",
        "auth_time",
        "amr",
        "idp",
        "nonce",
        "name",
        "nickname",
        "preferred_username",
        "given_name",
        "middle_name",
        "family_name",
        "email",
        "email_verified",
        "profile",
        "zoneinfo",
        "locale",
        "address",
        "phone_number",
        "picture",
        "website",
        "gender",
        "birthdate",
        "updated_at",
        "at_hash",
        "c_hash"
    ],
    "code_challenge_methods_supported": ["S256"],
    "introspection_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/introspection",
    "introspection_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none"
    ],
    "revocation_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/revocation",
    "revocation_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none"
    ],
    "end_session_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/logout",
    "request_parameter_supported":
    True,
    "request_object_signing_alg_values_supported": [
        "HS256",
        "HS384",
        "HS512",
        "RS256",
        "RS384",
        "RS512",
        "ES256",
        "ES384",
        "ES512"
    ],
    "device_authorization_endpoint":
    TEST_DISCOVERED_AUTH_SERVER_BASE + "/device/authorize"  # noqa
}


def mocked_oidc_discovery(**kwargs):
    return TEST_FAKE_OIDC_DISCOVERY


class OidcBaseTestHarnessClientConfig(OidcAuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class OidcBaseTestHarnessAuthClient(OidcAuthClient):

    def __init__(self, client_config: OidcBaseTestHarnessClientConfig):
        super().__init__(client_config)
        self._test_client_config = client_config

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> \
            Tuple[dict, Optional[AuthBase]]:
        return raw_payload, None

    def login(self,
              requested_scopes=None,
              allow_open_browser=True,
              **kwargs) -> FileBackedOidcCredential:
        return FileBackedOidcCredential(data=TEST_FAKE_TOKEN_FILE_DATA)

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        return SimpleInMemoryRequestAuthenticator(token_body=TEST_ACCESS_TOKEN)


def mocked_pem_load_error(key_data, **kwargs):
    return None


class AuthClientConfigBase(unittest.TestCase):

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
        under_test_literal = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        under_test_filebacked = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        self._assert_rsa_keys_equal(under_test_filebacked.private_key_data(),
                                    under_test_literal.private_key_data())

    def test_key_loads_with_or_without_password_literal(self):
        under_test_nopw = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        under_test_pw = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str,
            client_privkey_password=self.privkey_password)
        key_nopw = under_test_nopw.private_key_data()
        key_pw = under_test_pw.private_key_data()
        self._assert_rsa_keys_equal(key_pw, key_nopw)

    def test_key_loads_with_or_without_password_filebacked(self):
        under_test_nopw = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        under_test_pw = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path,
            client_privkey_password=self.privkey_password)
        key_nopw = under_test_nopw.private_key_data()
        key_pw = under_test_pw.private_key_data()
        self._assert_rsa_keys_equal(key_pw, key_nopw)

    def test_bad_password_throws(self):
        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password=None,
            client_privkey=self.privkey_literal_str)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password='bad password',
            client_privkey=self.privkey_literal_str)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password=None,
            client_privkey_file=self.privkey_file_path)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_password='bad password',
            client_privkey_file=self.privkey_file_path)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

    @mock.patch(
        'cryptography.hazmat.primitives.serialization.load_pem_private_key',
        mocked_pem_load_error)  # noqa
    def test_unexpected_keyload_restult(self):
        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey=self.privkey_literal_str_nopassword)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

        under_test = OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

    def test_no_key_configured(self):
        under_test = OidcAuthClientConfig(auth_server=TEST_AUTH_SERVER,
                                          client_id=TEST_CLIENT_ID,
                                          client_privkey=None,
                                          client_privkey_file=None,
                                          client_privkey_password=None)
        with self.assertRaises(AuthClientConfigException):
            under_test.private_key_data()

    def test_lazy_load_only_once(self):
        # FIXME: wrapping the object in this way doesn't seem to actually
        #   catch call counts for internal method calls.  Stepping through
        #   debugger seems to indicate proper behavior.
        under_test = MagicMock(wraps=OidcAuthClientConfig(
            auth_server=TEST_AUTH_SERVER,
            client_id=TEST_CLIENT_ID,
            client_privkey_file=self.privkey_file_path_nopassword))
        self.assertEqual(0, under_test._load_private_key.call_count)
        under_test.private_key_data()
        # self.assertEqual(1, under_test._load_private_key.call_count)
        under_test.private_key_data()
        # self.assertEqual(1, under_test._load_private_key.call_count)


@mock.patch(
    'planet.auth.oidc.api_clients.discovery_api_client.DiscoveryApiClient.discovery',  # noqa
    side_effect=mocked_oidc_discovery)
class AuthClientBaseTest(unittest.TestCase):

    def setUp(self):
        self.defaults_under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID))
        self.oidc_test_credential = FileBackedOidcCredential(
            data=TEST_FAKE_TOKEN_FILE_DATA)

    def test_oidc_discovery_override_authorization(self, mocked_discovery):
        # OIDC discovery is intended to be JIT in the base class.
        # When an override is provided, 1) that discovery should not happen
        # (some OIDC providers don't offer discovery, so it would fail),
        # and 2) the override should be used, even if discovery was
        # previously successful for another endpoint.
        #
        # This should be tested for each endpoint we support:
        #   authorization_endpoint  (This one is an oddball, since it doesn't
        #                            make HTTP requests the same way)
        #   introspection_endpoint
        #   jwks_endpoint
        #   revocation_endpoint
        #   token_endpoint

        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                authorization_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/authorize'))
        api_client = under_test._authorization_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/authorize',
                         api_client._authorization_uri)
        self.assertEqual(0, mocked_discovery.call_count)

        # discovery after the initial overridden client fetch (above) tests
        # that it's not clobbered by discovery
        under_test._discovery()
        api_client = under_test._authorization_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/authorize',
                         api_client._authorization_uri)

        # Discovery before the initial fetch test that it's not preempted by
        # a prior discovery.
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                authorization_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/authorize'))
        under_test._discovery()
        api_client = under_test._authorization_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/authorize',
                         api_client._authorization_uri)

        # And finally, test default behavior:
        default_api_client = self.defaults_under_test._authorization_client()
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE + '/authorize',
                         default_api_client._authorization_uri)

    def test_oidc_discovery_override_introspection(self, mocked_discovery):
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                introspection_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/introspection'))
        api_client = under_test._introspection_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/introspection',
                         api_client._endpoint_uri)
        self.assertEqual(0, mocked_discovery.call_count)

        # discovery after the initial overridden client fetch (above) tests
        # that it's not clobbered by discovery
        under_test._discovery()
        api_client = under_test._introspection_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/introspection',
                         api_client._endpoint_uri)

        # Discovery before the initial fetch test that it's not preempted by
        # a prior discovery.
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                introspection_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/introspection'))
        under_test._discovery()
        api_client = under_test._introspection_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/introspection',
                         api_client._endpoint_uri)

        # And finally, test default behavior:
        default_api_client = self.defaults_under_test._introspection_client()
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE + '/introspection',
                         default_api_client._endpoint_uri)

    def test_oidc_discovery_override_jwks(self, mocked_discovery):
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                jwks_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE + '/jwks'))
        api_client = under_test._jwks_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/jwks',
                         api_client._endpoint_uri)
        self.assertEqual(0, mocked_discovery.call_count)

        # discovery after the initial overridden client fetch (above) tests
        # that it's not clobbered by discovery
        under_test._discovery()
        api_client = under_test._jwks_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/jwks',
                         api_client._endpoint_uri)

        # Discovery before the initial fetch test that it's not preempted by
        # a prior discovery.
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                jwks_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE + '/jwks'))
        under_test._discovery()
        api_client = under_test._jwks_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/jwks',
                         api_client._endpoint_uri)

        # And finally, test default behavior:
        default_api_client = self.defaults_under_test._jwks_client()
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE + '/jwks',
                         default_api_client._endpoint_uri)

    def test_oidc_discovery_override_revocation(self, mocked_discovery):
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                revocation_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/revocation'))
        api_client = under_test._revocation_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/revocation',
                         api_client._endpoint_uri)
        self.assertEqual(0, mocked_discovery.call_count)

        # discovery after the initial overridden client fetch (above) tests
        # that it's not clobbered by discovery
        under_test._discovery()
        api_client = under_test._revocation_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/revocation',
                         api_client._endpoint_uri)

        # Discovery before the initial fetch test that it's not preempted by
        # a prior discovery.
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                revocation_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE +
                '/revocation'))
        under_test._discovery()
        api_client = under_test._revocation_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/revocation',
                         api_client._endpoint_uri)

        # And finally, test default behavior:
        default_api_client = self.defaults_under_test._revocation_client()
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE + '/revocation',
                         default_api_client._endpoint_uri)

    def test_oidc_discovery_override_token(self, mocked_discovery):
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                token_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE + '/token'))
        api_client = under_test._token_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/token',
                         api_client._endpoint_uri)
        self.assertEqual(0, mocked_discovery.call_count)

        # discovery after the initial overridden client fetch (above) tests
        # that it's not clobbered by discovery
        under_test._discovery()
        api_client = under_test._token_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/token',
                         api_client._endpoint_uri)

        # Discovery before the initial fetch test that it's not preempted by
        # a prior discovery.
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                token_endpoint=TEST_OVERRIDE_AUTH_SERVER_BASE + '/token'))
        under_test._discovery()
        api_client = under_test._token_client()
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/token',
                         api_client._endpoint_uri)

        # And finally, test default behavior:
        default_api_client = self.defaults_under_test._token_client()
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE + '/token',
                         default_api_client._endpoint_uri)

    def test_issuer_discovery_override(self, mocked_discovery):
        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID,
                issuer=TEST_OVERRIDE_AUTH_SERVER_BASE + '/override_issuer'))
        self.assertEqual(TEST_OVERRIDE_AUTH_SERVER_BASE + '/override_issuer',
                         under_test._issuer())
        self.assertEqual(0, mocked_discovery.call_count)

        under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID))
        self.assertEqual(TEST_DISCOVERED_AUTH_SERVER_BASE,
                         under_test._issuer())
        self.assertEqual(1, mocked_discovery.call_count)

        # second call doesn't re-do discovery
        under_test._issuer()
        self.assertEqual(1, mocked_discovery.call_count)

    def test_token_validator_created_once(self, mocked_discovery):
        under_test = self.defaults_under_test
        token_validator = under_test._token_validator()
        self.assertIsNotNone(token_validator)
        token_validator2 = under_test._token_validator()
        self.assertEqual(token_validator, token_validator2)

    #
    # The base client implementation of the following is pretty much
    # one liner pass through.  These nothing-burger tests are mostly
    # to goose the coverage targets, and would really only catch
    # gross errors in the pass through implementation. These are
    # better tested in end-to-end tests.
    #
    @mock.patch(
        'planet.auth.oidc.api_clients.token_api_client.TokenApiClient.get_token_from_refresh'  # noqa
    )
    def test_refresh(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        credential = under_test.refresh(
            self.oidc_test_credential.refresh_token())
        self.assertIsInstance(credential, FileBackedOidcCredential)
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.api_clients.introspect_api_client.IntrospectionApiClient.validate_access_token'  # noqa
    )
    def test_validate_access_token(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.validate_access_token(
            self.oidc_test_credential.access_token())
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.token_validator.TokenValidator.validate_token')
    def test_validate_access_token_local(self,
                                         mock_validate_token,
                                         mocked_discovery):
        under_test = self.defaults_under_test
        under_test.validate_access_token_local(
            self.oidc_test_credential.access_token(),
            required_audience="req_audience")
        self.assertEqual(1, mock_validate_token.call_count)

    # Leaving this test commented out until I clean up some of the code
    # under test here.
    # @mock.patch(
    #     'planet.auth.oidc.token_validator.TokenValidator.validate_token')
    # def test_validate_access_token_local_default_audience_from_config(
    #         self, mock_validate_token, mocked_discovery):
    #     under_test = self.defaults_under_test
    #     under_test.validate_access_token_local(
    #         self.oidc_test_credential.access_token(),
    #         required_audience=None)
    #     self.assertEqual(1, mock_validate_token.call_count)

    @mock.patch(
        'planet.auth.oidc.api_clients.introspect_api_client.IntrospectionApiClient.validate_id_token'  # noqa
    )
    def test_validate_id_token(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.validate_id_token(self.oidc_test_credential.id_token())
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.token_validator.TokenValidator.validate_id_token')
    def test_validate_id_token_local(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.validate_id_token_local(
            self.oidc_test_credential.id_token())
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.api_clients.introspect_api_client.IntrospectionApiClient.validate_refresh_token'  # noqa
    )
    def test_validate_refresh_token(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.validate_refresh_token(
            self.oidc_test_credential.refresh_token())
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.api_clients.revocation_api_client.RevocationApiClient.revoke_access_token'  # noqa
    )
    def test_revoke_access_token(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.revoke_access_token(
            self.oidc_test_credential.access_token())
        self.assertEqual(1, mock_api_client.call_count)

    @mock.patch(
        'planet.auth.oidc.api_clients.revocation_api_client.RevocationApiClient.revoke_refresh_token'  # noqa
    )
    def test_revoke_refresh_token(self, mock_api_client, mocked_discovery):
        under_test = self.defaults_under_test
        under_test.revoke_refresh_token(
            self.oidc_test_credential.refresh_token())
        self.assertEqual(1, mock_api_client.call_count)

    def test_get_scopes(self, mocked_discovery):
        under_test = self.defaults_under_test
        test_scopes = under_test.get_scopes()
        self.assertEqual(TEST_FAKE_OIDC_DISCOVERY['scopes_supported'],
                         test_scopes)
