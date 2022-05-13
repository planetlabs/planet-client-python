from unittest.mock import MagicMock

import pathlib
import tempfile
import time
import unittest
import uuid

from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.oidc.api_clients.token_api_client import TokenApiException
from planet.auth.oidc.auth_client import OidcAuthClient, OidcAuthClientConfig
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.oidc.request_authenticator import \
    RefreshingOidcTokenRequestAuthenticator, \
    RefreshOrReloginOidcTokenRequestAuthenticator
from planet.auth.request_authenticator import RequestAuthenticator
from tests.unit.auth.util import TestTokenBuilder
from tests.util import tdata_resource_file_path

TEST_TOKEN_TTL = 8
TEST_AUTH_SERVER = 'https://blackhole.unittest.planet.com/oauth2'
TEST_CLIENT_ID = '_TEST_CLIENT_ID_'


class StubOidcClientConfig(OidcAuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(TEST_AUTH_SERVER, TEST_CLIENT_ID, **kwargs)
        self.ttl = TEST_TOKEN_TTL
        self.token_signing_key_file = tdata_resource_file_path(
            'keys/keypair1_priv_nopassword.test_pem')


class StubOidcAuthClient(OidcAuthClient):

    def __init__(self, client_config: StubOidcClientConfig):
        super().__init__(client_config)
        self._mock_client_config = client_config
        self._refresh_state = {}
        self.token_builder = TestTokenBuilder(
            self._mock_client_config.token_signing_key_file)

    def _construct_oidc_credential(self,
                                   get_access_token,
                                   get_id_token,
                                   get_refresh_token):
        jwt_access_token = self.token_builder.construct_oidc_access_token(
            self._mock_client_config.ttl)
        jwt_id_token = self.token_builder.construct_oidc_access_token(
            self._mock_client_config.ttl)

        credential_data = {
            "token_type": "Bearer",
            "expires_in": self._mock_client_config.ttl,
            "scope": "offline_access profile openid planet"
        }
        if get_access_token:
            credential_data['access_token'] = jwt_access_token
        if get_id_token:
            credential_data['id_token'] = jwt_id_token
        if get_refresh_token:
            refresh_token = str(uuid.uuid4())
            credential_data['refresh_token'] = refresh_token
            self._refresh_state[refresh_token] = {
                'get_id_token': get_id_token,
                'get_access_token': get_access_token
            }

        credential = FileBackedOidcCredential(data=credential_data)
        return credential

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> \
            Tuple[dict, Optional[AuthBase]]:
        # return raw_payload, None
        # Abstract in the base class. Not under test here.
        assert 0

    def login(self,
              requested_scopes=None,
              allow_open_browser=False,
              get_access_token=True,
              get_id_token=True,
              get_refresh_token=True,
              **kwargs) -> FileBackedOidcCredential:
        return self._construct_oidc_credential(
            get_access_token=get_access_token,
            get_id_token=get_id_token,
            get_refresh_token=get_refresh_token)

    def refresh(self, refresh_token, requested_scopes=None, **kwargs):
        if refresh_token:
            return self._construct_oidc_credential(
                get_refresh_token=True,
                get_access_token=self._refresh_state[refresh_token]
                ['get_access_token'],
                get_id_token=self._refresh_state[refresh_token]
                ['get_id_token'])
        else:
            # raise AuthClientException("cannot refresh without refresh token")
            raise TokenApiException("cannot refresh without refresh token")

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        # return RefreshingOidcTokenRequestAuthenticator(
        #    credential_file=FileBackedOidcCredential(credential_file=credential_file_path),
        #    auth_client=self)
        # Abstract in the base class. Not under test here.
        assert 0


class RefreshFailingStubOidcAuthClient(StubOidcAuthClient):

    def refresh(self, refresh_token, requested_scopes=None, **kwargs):
        raise Exception("Forced test exception")


class RefreshingOidcRequestAuthenticatorTest(unittest.TestCase):

    def setUp(self):
        # we use the stub auth client for generating initial state, and the
        # mock auth client for probing authenticator behavior.
        self.stub_auth_client = StubOidcAuthClient(StubOidcClientConfig())
        self.wrapped_stub_auth_client = MagicMock(wraps=self.stub_auth_client)
        self.refresh_failing_auth_client = RefreshFailingStubOidcAuthClient(
            StubOidcClientConfig())
        self.wrapper_refresh_failing_auth_client = MagicMock(
            wraps=self.refresh_failing_auth_client)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = pathlib.Path(self.tmp_dir.name)

    def under_test_happy_path(self):
        credential_path = self.tmp_dir_path / 'refreshing_oidc_authenticator_test_token__with_refresh.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, self.stub_auth_client)
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=test_credential,
            auth_client=self.wrapped_stub_auth_client)

    def under_test_no_refresh_token(self):
        credential_path = self.tmp_dir_path / 'refreshing_oidc_authenticator_test_token__without_refresh.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, self.stub_auth_client, get_refresh_token=False)
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=test_credential,
            auth_client=self.wrapped_stub_auth_client)

    def under_test_no_auth_client(self):
        credential_path = self.tmp_dir_path / 'refreshing_oidc_authenticator_test_token__no_client_provided.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, self.stub_auth_client)
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=test_credential, auth_client=None)

    def under_test_no_access_token(self):
        credential_path = self.tmp_dir_path / 'refreshing_oidc_authenticator_test_token__no_access_token.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, self.stub_auth_client, get_access_token=False)
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=test_credential,
            auth_client=self.wrapped_stub_auth_client)

    def under_test_refresh_fails(self):
        credential_path = self.tmp_dir_path / 'refreshing_oidc_authenticator_test_token__refresh_fails.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, self.refresh_failing_auth_client)
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=test_credential,
            auth_client=self.wrapper_refresh_failing_auth_client)

    @staticmethod
    def mock_auth_login_and_command_initialize(credential_path,
                                               auth_client,
                                               get_access_token=True,
                                               get_id_token=True,
                                               get_refresh_token=True):
        # pretend to bootstrap client auth configuration on disk, the way
        # it may be used by a user in an interactive shell:

        # bash$ planet auth login
        test_credential = auth_client.login(
            get_access_token=get_access_token,
            get_refresh_token=get_refresh_token,
            get_id_token=get_id_token)
        test_credential.set_path(credential_path)
        test_credential.save()
        # <planet auth login process exits>

        # bash$ planet <some API command>
        #       # sets up credential object to be lazy loaded.
        test_credential = FileBackedOidcCredential(
            credential_file=credential_path)
        #       # The command would then use this credential and an
        #       # authenticator to interact with a planet API. Take it away,
        #       # test case...
        return test_credential

    @staticmethod
    def mock_api_call(under_test):
        # We don't need to actually mock making an HTTP API call. That is all
        # unit tested with the base class, and the OIDC authenticators don't
        # actually touch that. They only interact via the base class
        # pre_request_hook()
        under_test.pre_request_hook()

    def test_happy_path_1(self):
        # The first API call should trigger a token load from disk.
        # If the token is current, the auth client should be untouched.
        under_test = self.under_test_happy_path()

        self.assertIsNone(under_test._oidc_credentials.data())
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        # inside the refresh window, more access should not refresh
        self.mock_api_call(under_test)
        self.mock_api_call(under_test)
        self.mock_api_call(under_test)
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(access_token_t1, access_token_t2)

        # When the token reaches the 3/4 life, the authenticator should
        # attempt a token refresh
        time.sleep(((3 * TEST_TOKEN_TTL) / 4) + 2)
        self.mock_api_call(under_test)
        self.assertEqual(1, under_test._auth_client.refresh.call_count)
        access_token_t3 = under_test._oidc_credentials.access_token()
        self.assertNotEqual(access_token_t1, access_token_t3)

    def test_happy_path_2(self):
        # The first API call should trigger a token load.
        # If the token is past the refresh time, a token refresh should be
        # attempted before the first use
        under_test = self.under_test_happy_path()

        time.sleep(TEST_TOKEN_TTL + 2)
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(1, under_test._auth_client.refresh.call_count)

    def test_refresh_fails(self):
        # Refresh could fail.  If it does, this should be buried and we
        # should try to carry on with the token we have.
        # (this is why we refresh before expiry, so transient failures
        # do not stop work). Of course, eventually the token will be no good,
        # and this is expected to generate API errors.
        under_test = self.under_test_refresh_fails()

        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.mock_api_call(under_test)
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        self.assertEqual(1, under_test._auth_client.refresh.call_count)
        access_token_t2 = under_test._oidc_credentials.access_token()

        self.assertEqual(access_token_t1, access_token_t2)

    def test_no_refresh_token(self):
        # if we have no refresh token, what happens when we expect to
        # refresh? It's not expected that a user use the refreshing
        # authenticator when not using a refresh token (there is another
        # authenticator for this), but you never know what people will do.
        # This should be treated like any other refresh failure (above).
        # We continue with what we have. (and while we would never expect a
        # call to refresh to work without a refresh token, that decision is
        # delegated to the auth server.)
        under_test = self.under_test_no_refresh_token()

        self.mock_api_call(under_test)
        access_token_t1 = under_test._oidc_credentials.access_token()
        self.assertEqual(0, under_test._auth_client.refresh.call_count)

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        self.assertEqual(1, under_test._auth_client.refresh.call_count)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(access_token_t1, access_token_t2)

    def test_no_auth_client(self):
        # when no auth client is provided, just authenticate with what we
        # have.
        under_test = self.under_test_no_auth_client()

        self.mock_api_call(under_test)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(access_token_t1, access_token_t2)

    def test_no_access_token(self):
        # Test credential has no access token, but it does have a refresh
        # token. We would not expect clients that want to use APIs to have
        # such credentials, but you never know what people will try!
        # It's up to the API endpoint to decide if "no auth" is valid.
        # For some endpoints, this may be valid (e.g. public discovery
        # endpoints.)
        #
        # This is not expected to be a normal path, but we should behave.
        # It allows an application to potentially be bootstrap with just
        # a refresh token.
        under_test = self.under_test_no_access_token()
        access_token_t1 = under_test._oidc_credentials.access_token()
        self.assertIsNone(access_token_t1)
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.mock_api_call(under_test)
        self.assertEqual(1, under_test._auth_client.refresh.call_count)

    def test_out_of_band_update_1(self):
        # Out of band credential update.  We expect the refresher to reload
        # the credential file without attempting a refresh.
        under_test = self.under_test_happy_path()

        self.assertIsNone(under_test._oidc_credentials.data())
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        credential_t1 = under_test._oidc_credentials
        oob_credential = self.stub_auth_client.refresh(
            credential_t1.refresh_token())
        oob_credential.set_path(credential_t1.path())
        oob_credential.save()
        access_token_oob = oob_credential.access_token()

        # The new token is within TTL, and a refresh should not occure
        self.mock_api_call(under_test)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.assertNotEqual(access_token_t1, access_token_t2)
        self.assertEqual(access_token_oob, access_token_t2)

    def test_out_of_band_update_2(self):
        # Out of band credential update.  We expect the refresher to reload
        # the credential file without attempting a refresh.
        under_test = self.under_test_happy_path()

        self.assertIsNone(under_test._oidc_credentials.data())
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        credential_t1 = under_test._oidc_credentials
        oob_credential = self.stub_auth_client.refresh(
            credential_t1.refresh_token())
        oob_credential.set_path(credential_t1.path())
        oob_credential.save()
        access_token_oob = oob_credential.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        # The new token is outside TTL, even after the token is reloaded, this
        # should be detected and a refresh should still occur.
        self.mock_api_call(under_test)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(1, under_test._auth_client.refresh.call_count)
        self.assertNotEqual(access_token_t1, access_token_t2)
        self.assertNotEqual(access_token_oob, access_token_t2)


class RefreshOrReloginOidcRequestAuthenticatorTest(unittest.TestCase):

    def setUp(self):
        # we use the stub auth client for generating initial state, and the
        # mock auth client for probing authenticator behavior.
        self.stub_auth_client = StubOidcAuthClient(StubOidcClientConfig())
        self.mock_auth_client = MagicMock(wraps=self.stub_auth_client)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = pathlib.Path(self.tmp_dir.name)

    def under_test_with_refresh_token(self):
        credential_path = self.tmp_dir_path / 'refreshing_or_relogin_oidc_authenticator_test_token__with_refresh.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path)
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=test_credential, auth_client=self.mock_auth_client)

    def under_test_without_refresh_token(self):
        credential_path = self.tmp_dir_path / 'refreshing_or_relogin_oidc_authenticator_test_token__without_refresh.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path, get_refresh_token=False)
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=test_credential, auth_client=self.mock_auth_client)

    def under_test_no_auth_client(self):
        credential_path = self.tmp_dir_path / 'refreshing_or_relogin_oidc_authenticator_test_token__no_client_provided.json'  # noqa
        test_credential = self.mock_auth_login_and_command_initialize(
            credential_path)
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=test_credential, auth_client=None)

    def mock_auth_login_and_command_initialize(self,
                                               credential_path,
                                               get_access_token=True,
                                               get_id_token=True,
                                               get_refresh_token=True):
        # pretend to bootstrap client auth configuration on disk, the way
        # it may be used by a user in an interactive shell:

        # bash$ planet auth login
        test_credential = self.stub_auth_client.login(
            get_access_token=get_access_token,
            get_refresh_token=get_refresh_token,
            get_id_token=get_id_token)
        test_credential.set_path(credential_path)
        test_credential.save()
        # <planet auth login process exits>

        # bash$ planet <some API command>
        #       # sets up credential object to be lazy loaded.
        test_credential = FileBackedOidcCredential(
            credential_file=credential_path)
        #       # The command would then use this credential and an
        #       # authenticator to interact with a planet API. Take it away,
        #       # test case...
        return test_credential

    def mock_api_call(self, under_test):
        # We don't need to actually mock making an HTTP API call. That is all
        # unit tested with the base class, and the OIDC authenticators don't
        # actually touch that. They only interact via the base class
        # pre_request_hook()
        under_test.pre_request_hook()

    def test_refresh_token_calls_refresh(self):
        under_test = self.under_test_with_refresh_token()

        self.assertIsNone(under_test._oidc_credentials.data())
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.assertEqual(0, under_test._auth_client.login.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        self.assertEqual(1, under_test._auth_client.refresh.call_count)
        self.assertEqual(0, under_test._auth_client.login.call_count)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertNotEqual(access_token_t1, access_token_t2)

    def test_no_refresh_token_calls_login(self):
        under_test = self.under_test_without_refresh_token()

        self.assertIsNone(under_test._oidc_credentials.data())
        self.mock_api_call(under_test)
        self.assertIsNotNone(under_test._oidc_credentials.data())
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.assertEqual(0, under_test._auth_client.login.call_count)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        self.assertEqual(0, under_test._auth_client.refresh.call_count)
        self.assertEqual(1, under_test._auth_client.login.call_count)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertNotEqual(access_token_t1, access_token_t2)

    def test_no_auth_client(self):
        # when no auth client is provided, just authenticate with what we
        # have.
        under_test = self.under_test_no_auth_client()

        self.mock_api_call(under_test)
        access_token_t1 = under_test._oidc_credentials.access_token()

        time.sleep(TEST_TOKEN_TTL + 2)

        self.mock_api_call(under_test)
        access_token_t2 = under_test._oidc_credentials.access_token()
        self.assertEqual(access_token_t1, access_token_t2)
