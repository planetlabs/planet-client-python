from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.oidc.api_clients.oidc_request_auth import prepare_client_noauth_auth_payload
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_token import FileBackedOidcToken


# XXX Cleanly, this should probably share a base class with
#     AuthCodePKCEClientConfig - "BrowserFlowClientConfig", "UserInteractiveFlow", or something.
#     But, implicit flow is really only intended for legacy browser clients,
#     and this python lib implementation really only exists to study the
#     OIDC server
class ImplicitClientConfig(OidcAuthClientConfig):
    def __init__(self,
                 redirect_uri,
                 request_access_token=True,
                 request_id_token=True,
                 **kwargs):
        super().__init__(**kwargs)
        self.request_access_token = request_access_token
        self.request_id_token = request_id_token
        self.redirect_uri = redirect_uri


class ImplicitAuthClient(OidcAuthClient):
    def __init__(self, client_config: ImplicitClientConfig):
        super().__init__(client_config)
        self._implicit_client_config = client_config

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> Tuple[dict, Optional[AuthBase]]:
        # FIXME: test, is putting the client id in the auth header and the payload overconstrained?
        #        Is that the job of this class, or the helper to fix?
        #        So ugly we are getting into the business of the api clients.
        # FIXME: should removing a redundant client_id be the job of the helper?
        # FIXME: make the payload union part of the helper?
        auth_payload = prepare_client_noauth_auth_payload(client_id=self._implicit_client_config.client_id)
        # enriched_payload = raw_payload | auth_payload  # Python >= 3.9
        enriched_payload = {**raw_payload, **auth_payload}  # Python >= 3.5
        return enriched_payload, None

    def login(self, requested_scopes=None, allow_open_browser=True, **kwargs):
        if not requested_scopes:
            requested_scopes = self._implicit_client_config.default_request_scopes

        if allow_open_browser:
            return FileBackedOidcToken(
                self._authorization_client().token_from_implicit_flow_with_browser_without_callback_listener(
                    self._implicit_client_config.client_id,
                    self._implicit_client_config.redirect_uri,
                    requested_scopes,
                    self._implicit_client_config.request_access_token,
                    self._implicit_client_config.request_id_token
                ))
        else:
            return FileBackedOidcToken(
                self._authorization_client().token_from_implicit_flow_without_browser_without_callback_listener(
                    self._implicit_client_config.client_id,
                    self._implicit_client_config.redirect_uri,
                    requested_scopes,
                    self._implicit_client_config.request_access_token,
                    self._implicit_client_config.request_id_token
                ))
