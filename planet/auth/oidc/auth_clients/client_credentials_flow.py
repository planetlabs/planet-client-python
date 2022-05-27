import pathlib
from abc import ABC

from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.auth_client import AuthClientConfigException
from planet.auth.oidc.api_clients.oidc_request_auth import \
    prepare_client_secret_request_auth, \
    prepare_private_key_assertion_auth_payload, \
    prepare_client_secret_auth_payload
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.oidc.request_authenticator import \
    RefreshOrReloginOidcTokenRequestAuthenticator


class ClientCredentialsClientSecretClientConfig(OidcAuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client_secret:
            raise AuthClientConfigException(
                'client_secret must be configured for client'
                ' credentials client secret client.')


class ClientCredentialsAuthClientBase(OidcAuthClient, ABC):

    def default_request_authenticator(
        self, credential_file_path: pathlib.Path
    ) -> RefreshOrReloginOidcTokenRequestAuthenticator:
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=FileBackedOidcCredential(
                credential_file=credential_file_path),
            auth_client=self)


class ClientCredentialsClientSecretAuthClient(ClientCredentialsAuthClientBase):

    def __init__(self,
                 client_config: ClientCredentialsClientSecretClientConfig):
        super().__init__(client_config)
        self._ccauth_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        return raw_payload, prepare_client_secret_request_auth(
            self._oidc_client_config.client_id,
            self._oidc_client_config.client_secret)

    # With client credentials and a simple client secret, the auth server
    # insists that we put the secret in the payload during the initial
    # token request.  For other commands (e.g. token validate) it permits
    # us to send it an an auth header.  We prefer this as the default since
    # an auth header should be less likely to land in a log than URL
    # parameters or request payloads.
    def _client_auth_enricher_login(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        auth_payload = prepare_client_secret_auth_payload(
            client_id=self._oidc_client_config.client_id,
            client_secret=self._oidc_client_config.client_secret)
        enriched_payload = {**raw_payload, **auth_payload}
        return enriched_payload, None

    def login(self,
              requested_scopes=None,
              requested_audiences=None,
              allow_open_browser=False,
              **kwargs):
        if not requested_scopes:
            requested_scopes = \
                self._ccauth_client_config.default_request_scopes

        if not requested_audiences:
            requested_audiences = \
                self._ccauth_client_config.default_request_audiences

        return FileBackedOidcCredential(
            self._token_client().get_token_from_client_credentials(
                client_id=self._ccauth_client_config.client_id,
                requested_scopes=requested_scopes,
                requested_audiences=requested_audiences,
                auth_enricher=self._client_auth_enricher_login))


class ClientCredentialsPubKeyClientConfig(OidcAuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client_privkey and not self.client_privkey_file:
            raise AuthClientConfigException(
                'One of client_privkey or client_privkey_file must be'
                ' configured for client credentials public key client')


class ClientCredentialsPubKeyAuthClient(ClientCredentialsAuthClientBase):

    def __init__(self, client_config: ClientCredentialsPubKeyClientConfig):
        super().__init__(client_config)
        self._pubkey_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        auth_assertion_payload = prepare_private_key_assertion_auth_payload(
            audience=audience,
            client_id=self._oidc_client_config.client_id,
            private_key=self._oidc_client_config.private_key_data(),
            ttl=300)
        enriched_payload = {**raw_payload, **auth_assertion_payload}
        return enriched_payload, None

    def login(self,
              requested_scopes=None,
              requested_audiences=None,
              allow_open_browser=False,
              **kwargs):
        # FIXME: how much can we consolidate this common fallback
        #  to default in login() methods?
        if not requested_scopes:
            requested_scopes = \
                self._pubkey_client_config.default_request_scopes

        if not requested_audiences:
            requested_audiences = \
                self._pubkey_client_config.default_request_audiences

        return FileBackedOidcCredential(
            self._token_client().get_token_from_client_credentials(
                client_id=self._pubkey_client_config.client_id,
                requested_scopes=requested_scopes,
                requested_audiences=requested_audiences,
                auth_enricher=self._client_auth_enricher))
