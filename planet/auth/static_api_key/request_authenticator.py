from planet.auth.request_authenticator import RequestAuthenticator
from planet.auth.static_api_key.static_api_key import FileBackedApiKey


class FileBackedApiKeyRequestAuthenticator(RequestAuthenticator):
    """
    Load a bearer token from a file just in time for the request.
    Perform local checks on the validity of the token and throw
    if we think it will fail.
    """

    def __init__(self, auth_file: FileBackedApiKey):
        super().__init__(token_body='')
        self._auth_file = auth_file

    def pre_request_hook(self):
        self._auth_file.lazy_reload()
        self._token_body = self._auth_file.api_key()
        self._token_prefix = self._auth_file.bearer_token_prefix()
