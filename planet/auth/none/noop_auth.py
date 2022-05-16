import pathlib

from planet.auth.auth_client import AuthClientConfig, AuthClient
from planet.auth.credential import Credential
from planet.auth.request_authenticator import RequestAuthenticator, \
    SimpleInMemoryRequestAuthenticator


class NoOpCredential(Credential):

    def load(self):
        pass

    def save(self):
        pass


class NoOpAuthClientConfig(AuthClientConfig):
    pass


class NoOpAuthClient(AuthClient):

    def __init__(self, client_config: NoOpAuthClientConfig):
        super().__init__(client_config)
        self._noop_client_config = client_config

    def login(self, **kwargs) -> Credential:
        return NoOpCredential()

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        return SimpleInMemoryRequestAuthenticator(token_body=None)

    def refresh(self, refresh_token: str,
                requested_scopes: list[str]) -> Credential:
        return self.login()

    def validate_access_token(self, access_token: str):
        return {}

    def validate_id_token(self, id_token: str):
        return {}

    def validate_id_token_local(self, id_token: str):
        return {}

    def validate_refresh_token(self, refresh_token: str):
        return {}

    def revoke_access_token(self, access_token: str):
        pass

    def revoke_refresh_token(self, refresh_token: str):
        pass

    def get_scopes(self):
        return []
