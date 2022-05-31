import pathlib
import pytest
import unittest

import planet.auth
from planet.auth.auth_client import AuthClientConfig, AuthClient, \
    AuthClientException
from planet.auth.credential import Credential
from planet.auth.oidc.auth_clients.auth_code_flow import \
    AuthCodePKCEClientConfig, \
    AuthCodePKCEWithPubKeyClientConfig, \
    AuthCodePKCEWithClientSecretClientConfig
from planet.auth.oidc.auth_clients.client_credentials_flow import \
    ClientCredentialsClientSecretClientConfig, \
    ClientCredentialsPubKeyClientConfig
from planet.auth.oidc.auth_clients.resource_owner_flow import \
    ResourceOwnerClientConfig
from planet.auth.planet_legacy.auth_client import PlanetLegacyAuthClientConfig
from planet.auth.request_authenticator import \
    RequestAuthenticator
from planet.auth.static_api_key.auth_client import \
    StaticApiKeyAuthClientConfig
from planet.auth.none.noop_auth import NoOpAuthClientConfig
from tests.util import tdata_resource_file_path


class AuthClientConfigTestImpl(AuthClientConfig):
    pass


class AuthClientConfigInvalidImpl(AuthClientConfig):
    pass


class AuthClientTestImpl(AuthClient):

    def __init__(self, client_config: AuthClientConfigTestImpl):
        super().__init__(client_config)
        self._test_client_config = client_config

    def login(self, **kwargs) -> Credential:
        assert 0  # abstract method not under test

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        # return SimpleInMemoryRequestAuthenticator(token_body=None)
        assert 0  # abstract method not under test


class TestAuthClientBase(unittest.TestCase):

    def test_no_impl_exception(self):
        under_test = AuthClientTestImpl(AuthClientConfigTestImpl())

        with self.assertRaises(AuthClientException):
            under_test.refresh(None, None)

        with self.assertRaises(AuthClientException):
            under_test.validate_access_token(None)

        with self.assertRaises(AuthClientException):
            under_test.validate_access_token_local(None, None)

        with self.assertRaises(AuthClientException):
            under_test.validate_id_token(None)

        with self.assertRaises(AuthClientException):
            under_test.validate_id_token_local(None)

        with self.assertRaises(AuthClientException):
            under_test.validate_refresh_token(None)

        with self.assertRaises(AuthClientException):
            under_test.revoke_access_token(None)

        with self.assertRaises(AuthClientException):
            under_test.revoke_refresh_token(None)

        with self.assertRaises(AuthClientException):
            under_test.get_scopes()


class ClientFactoryTest(unittest.TestCase):

    def test_create_pkce_auth_code_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                AuthCodePKCEClientConfig(auth_server='dummy',
                                         client_id='dummy',
                                         redirect_uri='dummy')),
            planet.auth.oidc.auth_clients.auth_code_flow.AuthCodePKCEAuthClient
        )

    def test_create_pkce_auth_code_client_secret_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                AuthCodePKCEWithClientSecretClientConfig(
                    auth_server='dummy',
                    client_id='dummy',
                    redirect_uri='dummy',
                    client_secret='dummy')),
            planet.auth.oidc.auth_clients.auth_code_flow.
            AuthCodePKCEWithClientSecretAuthClient)

    def test_create_pkce_auth_code_pubkey_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                AuthCodePKCEWithPubKeyClientConfig(auth_server='dummy',
                                                   client_id='dummy',
                                                   redirect_uri='dummy',
                                                   client_privkey='dummy')),
            planet.auth.oidc.auth_clients.auth_code_flow.
            AuthCodePKCEWithPubKeyAuthClient)

    def test_create_client_credentials_client_secret_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                ClientCredentialsClientSecretClientConfig(
                    auth_server='dummy',
                    client_id='dummy',
                    client_secret='dummy')),
            planet.auth.oidc.auth_clients.client_credentials_flow.
            ClientCredentialsClientSecretAuthClient)

    def test_create_client_credentials_pubkey_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                ClientCredentialsPubKeyClientConfig(auth_server='dummy',
                                                    client_id='dummy',
                                                    client_privkey='dummy')),
            planet.auth.oidc.auth_clients.client_credentials_flow.
            ClientCredentialsPubKeyAuthClient)

    @pytest.mark.skip('No implementation for resource owner client')
    def test_create_resource_owner_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                ResourceOwnerClientConfig(auth_server='dummy',
                                          client_id='dummy')),
            planet.auth.oidc.auth_clients.resource_owner_flow.
            ResourceOwnerAuthClient)

    def test_create_planet_legacy_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                PlanetLegacyAuthClientConfig(legacy_auth_endpoint='dummy')),
            planet.auth.planet_legacy.auth_client.PlanetLegacyAuthClient)

    def test_static_apikey_client(self):
        self.assertIsInstance(
            AuthClient.from_config(StaticApiKeyAuthClientConfig()),
            planet.auth.static_api_key.auth_client.StaticApiKeyAuthClient)

    def test_noop_client(self):
        self.assertIsInstance(
            AuthClient.from_config(
                NoOpAuthClientConfig(
                    extra_garbage_to_ignore='some_test_trash')),
            planet.auth.none.noop_auth.NoOpAuthClient)

    def test_invalid_config_type(self):
        with self.assertRaises(AuthClientException):
            AuthClient.from_config(AuthClientConfigInvalidImpl())


class ConfigFactoryTest(unittest.TestCase):

    def test_pkce_auth_code_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/pkce_auth_code.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config, AuthCodePKCEClientConfig)

    def test_pkce_auth_code_secret_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/pkce_auth_code_secret.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config,
                              AuthCodePKCEWithClientSecretClientConfig)

    def test_pkce_auth_code_pubkey_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/pkce_auth_code_pubkey.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config,
                              AuthCodePKCEWithPubKeyClientConfig)

    def test_client_credentials_client_secret_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/client_credentials_client_secret.json'  # noqa
        )
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config,
                              ClientCredentialsClientSecretClientConfig)

    def test_client_credentials_pubkey_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/client_credentials_pubkey_file.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config,
                              ClientCredentialsPubKeyClientConfig)

    @pytest.mark.skip('No implementation for resource owner client')
    def test_resource_owner_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/resource_owner.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config, ResourceOwnerClientConfig)

    def test_static_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/static_api_key.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config, StaticApiKeyAuthClientConfig)

    def test_noop_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/none.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config, NoOpAuthClientConfig)

    def test_planet_legacy_config_from_file(self):
        file_path = tdata_resource_file_path(
            'auth_client_configs/utest/planet_legacy.json')
        auth_client_config = AuthClientConfig.from_file(file_path)
        self.assertIsInstance(auth_client_config, PlanetLegacyAuthClientConfig)

    def test_invalid_config_type(self):
        with self.assertRaises(AuthClientException):
            AuthClientConfig.from_dict({'client_type': '__test_invalid__'})
