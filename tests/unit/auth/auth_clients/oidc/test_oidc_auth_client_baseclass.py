import pathlib
import unittest
from typing import Tuple, Optional
from unittest import mock

from requests.auth import AuthBase

from planet.auth.oidc.auth_client import OidcAuthClient, OidcAuthClientConfig
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.request_authenticator import RequestAuthenticator, \
    SimpleInMemoryRequestAuthenticator

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


@mock.patch(
    'planet.auth.oidc.api_clients.discovery_api_client.DiscoveryApiClient.discovery',  # noqa
    side_effect=mocked_oidc_discovery)
class TestAuthClientBase(unittest.TestCase):

    def setUp(self):
        self.defaults_under_test = OidcBaseTestHarnessAuthClient(
            OidcBaseTestHarnessClientConfig(
                auth_server=TEST_DISCOVERED_AUTH_SERVER_BASE,
                client_id=TEST_CLIENT_ID))

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
