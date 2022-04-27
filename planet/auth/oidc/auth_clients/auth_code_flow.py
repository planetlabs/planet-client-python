import pathlib
from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.oidc.api_clients.oidc_request_auth import \
    prepare_client_noauth_auth_payload
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_token import FileBackedOidcToken
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


class AuthCodePKCEAuthClient(OidcAuthClient):

    def __init__(self, client_config: AuthCodePKCEClientConfig):
        super().__init__(client_config)
        self._authcode_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        auth_payload = prepare_client_noauth_auth_payload(
            client_id=self._authcode_client_config.client_id)
        # enriched_payload = raw_payload | auth_payload  # Python >= 3.9
        enriched_payload = {**raw_payload, **auth_payload}  # Python >= 3.5
        return enriched_payload, None

    def login(self, requested_scopes=None, allow_open_browser=True, **kwargs):
        if not requested_scopes:
            requested_scopes = \
                self._authcode_client_config.default_request_scopes

        pkce_code_verifier, pkce_code_challenge = \
            create_pkce_challenge_verifier_pair()
        if allow_open_browser:
            redirect_uri = self._authcode_client_config.local_redirect_uri
            authcode = self._authorization_client(
            ).authcode_from_pkce_flow_with_browser_with_callback_listener(
                self._authcode_client_config.client_id,
                redirect_uri,
                requested_scopes,
                pkce_code_challenge)
        else:
            redirect_uri = self._authcode_client_config.redirect_uri
            authcode = self._authorization_client(
            ).authcode_from_pkce_flow_without_browser_without_callback_listener(  # noqa
                self._authcode_client_config.client_id,
                redirect_uri,
                requested_scopes,
                pkce_code_challenge)

        token_json = self._token_client().get_token_from_code(
            redirect_uri,
            self._authcode_client_config.client_id,
            authcode,
            pkce_code_verifier)
        return FileBackedOidcToken(token_json)

    def default_request_authenticator(
        self, token_file_path: pathlib.Path
    ) -> RefreshingOidcTokenRequestAuthenticator:
        return RefreshingOidcTokenRequestAuthenticator(
            token_file=FileBackedOidcToken(token_file=token_file_path),
            auth_client=self)
