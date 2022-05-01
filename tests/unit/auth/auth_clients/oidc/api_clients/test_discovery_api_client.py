import json
import unittest

from requests.models import Response
from unittest import mock

from planet.auth.oidc.api_clients.discovery_api_client import \
    DiscoveryAPIClient

TEST_API_ENDPOINT = 'https://blackhole.unittest.planet.com/api'
API_RESPONSE_VALID = {
    "issuer":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7",
    "authorization_endpoint":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/authorize",
    "token_endpoint":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/token",
    "userinfo_endpoint":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/userinfo",
    "registration_endpoint":
    "https://account.planet.com/oauth2/v1/clients",
    "jwks_uri":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/keys",
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
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/introspect",
    "introspection_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none"
    ],
    "revocation_endpoint":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/revoke",
    "revocation_endpoint_auth_methods_supported": [
        "client_secret_basic",
        "client_secret_post",
        "client_secret_jwt",
        "private_key_jwt",
        "none"
    ],
    "end_session_endpoint":
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/logout",
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
    "https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7/v1/device/authorize"  # noqa
}
# API_RESPONSE_FAILED = {}


class MockRequests:
    request_counter = 0

    @staticmethod
    def mocked_response_ok(request_url, **kwargs):
        MockRequests.request_counter += 1
        response = Response()
        response.status_code = 200
        response.headers['content-type'] = 'application/json'
        response._content = str.encode(json.dumps(API_RESPONSE_VALID))
        return response


class DiscoveryApiClientTest(unittest.TestCase):

    @mock.patch('requests.get', side_effect=MockRequests.mocked_response_ok)
    def test_verify_caching(self, mock_get):
        self.assertEqual(0, MockRequests.request_counter)
        under_test = DiscoveryAPIClient(discovery_uri=TEST_API_ENDPOINT)
        json_response = under_test.discovery()
        self.assertEqual(API_RESPONSE_VALID, json_response)
        self.assertEqual(1, MockRequests.request_counter)
        under_test.discovery()
        self.assertEqual(1, MockRequests.request_counter)
