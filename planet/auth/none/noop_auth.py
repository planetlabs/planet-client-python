import pathlib

from planet.auth.auth_client import AuthClientConfig, AuthClient
from planet.auth.credential import Credential
from planet.auth.request_authenticator import RequestAuthenticator, \
    SimpleInMemoryRequestAuthenticator
from planet.auth.static_api_key.static_api_key import FileBackedApiKey


class NoOpAuthClientConfig(AuthClientConfig):
    pass


class NoOpAuthClient(AuthClient):

    def __init__(self, client_config: NoOpAuthClientConfig):
        super().__init__(client_config)
        self._noop_client_config = client_config

    def login(self, **kwargs) -> Credential:
        return FileBackedApiKey()

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        return SimpleInMemoryRequestAuthenticator(token_body=None)
