import pathlib

from planet.auth.auth_client import \
    AuthClient, \
    AuthClientConfig
from planet.auth.credential import \
    Credential
from planet.auth.static_api_key.request_authenticator import \
    FileBackedAPIKeyRequestAuthenticator
from planet.auth.static_api_key.static_api_key import \
    FileBackedAPIKey


class StaticApiKeyAuthClientConfig(AuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class StaticApiKeyAuthClient(AuthClient):

    def __init__(self, client_config: StaticApiKeyAuthClientConfig):
        super().__init__(client_config)

    def login(self, **kwargs) -> Credential:
        pass

    def default_request_authenticator(
            self, token_file_path: pathlib.Path
    ) -> FileBackedAPIKeyRequestAuthenticator:
        return FileBackedAPIKeyRequestAuthenticator(auth_file=FileBackedAPIKey(
            api_key_file=token_file_path))
