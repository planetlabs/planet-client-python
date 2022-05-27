import pathlib
from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.auth_client import AuthClientConfigException
from planet.auth.oidc.api_clients.oidc_request_auth import \
    prepare_client_noauth_auth_payload, \
    prepare_private_key_assertion_auth_payload, \
    prepare_client_secret_request_auth
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.oidc.request_authenticator import \
    RefreshingOidcTokenRequestAuthenticator
from planet.auth.oidc.util import create_pkce_challenge_verifier_pair


class AuthCodePKCEClientConfig(OidcAuthClientConfig):

    def __init__(self, redirect_uri, local_redirect_uri=None, **kwargs):
        super().__init__(**kwargs)
        # Redirect URI must match the client config on the OIDC service,
        # which may permit multiple values. We let our auth configs provide
        # different URLs for use cases where we either expect to configure a
        # redirect service locally, or expect it to be available remotely.
        # If only one is set, set both to the same value.
        self.redirect_uri = redirect_uri
        self.local_redirect_uri = local_redirect_uri
        if redirect_uri and not local_redirect_uri:
            self.local_redirect_uri = redirect_uri
        if local_redirect_uri and not redirect_uri:
            self.redirect_uri = local_redirect_uri

        if not self.redirect_uri:
            raise AuthClientConfigException(
                'A redirect_uri or local_redirect_uri is required for'
                ' PKCE auth code client.')


class AuthCodePKCEAuthClient(OidcAuthClient):

    def __init__(self, client_config: AuthCodePKCEClientConfig):
        super().__init__(client_config)
        self._authcode_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        auth_payload = prepare_client_noauth_auth_payload(
            client_id=self._oidc_client_config.client_id)
        enriched_payload = {**raw_payload, **auth_payload}
        return enriched_payload, None

    def login(self,
              requested_scopes=None,
              requested_audiences=None,
              allow_open_browser=True,
              **kwargs):
        if not requested_scopes:
            requested_scopes = \
                self._authcode_client_config.default_request_scopes

        if not requested_audiences:
            requested_audiences = \
                self._authcode_client_config.default_request_audiences

        pkce_code_verifier, pkce_code_challenge = \
            create_pkce_challenge_verifier_pair()
        if allow_open_browser:
            redirect_uri = self._authcode_client_config.local_redirect_uri
            authcode = self._authorization_client(
            ).authcode_from_pkce_flow_with_browser_with_callback_listener(
                client_id=self._authcode_client_config.client_id,
                redirect_uri=redirect_uri,
                requested_scopes=requested_scopes,
                requested_audiences=requested_audiences,
                pkce_code_challenge=pkce_code_challenge)
        else:
            redirect_uri = self._authcode_client_config.redirect_uri
            authcode = self._authorization_client(
            ).authcode_from_pkce_flow_without_browser_without_callback_listener(  # noqa
                client_id=self._authcode_client_config.client_id,
                redirect_uri=redirect_uri,
                requested_scopes=requested_scopes,
                requested_audiences=requested_audiences,
                pkce_code_challenge=pkce_code_challenge)

        token_json = self._token_client().get_token_from_code(
            redirect_uri=redirect_uri,
            client_id=self._authcode_client_config.client_id,
            code=authcode,
            code_verifier=pkce_code_verifier,
            auth_enricher=self._client_auth_enricher)
        return FileBackedOidcCredential(token_json)

    def default_request_authenticator(
        self, credential_file_path: pathlib.Path
    ) -> RefreshingOidcTokenRequestAuthenticator:
        return RefreshingOidcTokenRequestAuthenticator(
            credential_file=FileBackedOidcCredential(
                credential_file=credential_file_path),
            auth_client=self)


# client auth via secret or public/private keypair are optional for auth
# code flow clients. They are used when the client is "private"
class AuthCodePKCEWithClientSecretClientConfig(AuthCodePKCEClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client_secret:
            raise AuthClientConfigException(
                'client_secret must be configured for PKCE auth code'
                ' with client secret client')


class AuthCodePKCEWithClientSecretAuthClient(AuthCodePKCEAuthClient):

    def __init__(self,
                 client_config: AuthCodePKCEWithClientSecretClientConfig):
        super().__init__(client_config)

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        return raw_payload, prepare_client_secret_request_auth(
            self._oidc_client_config.client_id,
            self._oidc_client_config.client_secret)

    # def _client_auth_enricher(
    #         self, raw_payload: dict,
    #         audience: str) -> Tuple[dict, Optional[AuthBase]]:
    #     auth_assertion_payload = prepare_client_secret_auth_payload(
    #         self._oidc_client_config.client_id,
    #         self._oidc_client_config.client_secret)
    #     enriched_payload = {**raw_payload, **auth_assertion_payload}
    #     return enriched_payload, None


class AuthCodePKCEWithPubKeyClientConfig(AuthCodePKCEClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client_privkey and not self.client_privkey_file:
            raise AuthClientConfigException(
                'One of client_privkey or client_privkey_file must be'
                ' configured for PKCE auth code with public key client')


class AuthCodePKCEWithPubKeyAuthClient(AuthCodePKCEAuthClient):

    def __init__(self, client_config: AuthCodePKCEWithPubKeyClientConfig):
        super().__init__(client_config)

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
