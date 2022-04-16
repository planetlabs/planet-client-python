from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient


class ResourceOwnerClientConfig(OidcAuthClientConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise Exception('No implementation')


class ResourceOwnerAuthClient(OidcAuthClient):
    def __init__(self, client_config: ResourceOwnerClientConfig):
        super().__init__(client_config)
        self._resource_owner_client_config = client_config

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> Tuple[dict, Optional[AuthBase]]:
        raise Exception('No implementation')

    def login(self, requested_scopes=None, allow_open_browser=False):
        # if not requested_scopes:
        #     requested_scopes = self._resource_owner_client_config.default_request_scopes
        raise Exception('No implementation')
