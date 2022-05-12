import pathlib

from planet.auth.auth_client import \
    AuthClient, \
    AuthClientConfig
from planet.auth.credential import \
    Credential
from planet.auth.static_api_key.request_authenticator import \
    FileBackedApiKeyRequestAuthenticator
from planet.auth.static_api_key.static_api_key import \
    FileBackedApiKey


class StaticApiKeyAuthClientConfig(AuthClientConfig):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class StaticApiKeyAuthClient(AuthClient):

    def __init__(self, client_config: StaticApiKeyAuthClientConfig):
        super().__init__(client_config)

    def login(self, **kwargs) -> Credential:
        pass

    def default_request_authenticator(
            self, credential_file_path: pathlib.Path
    ) -> FileBackedApiKeyRequestAuthenticator:
        return FileBackedApiKeyRequestAuthenticator(auth_file=FileBackedApiKey(
            api_key_file=credential_file_path))
