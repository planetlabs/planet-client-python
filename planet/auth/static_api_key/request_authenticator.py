from planet.auth.request_authenticator import BearerTokenRequestAuthenticator
from planet.auth.static_api_key.static_api_key import FileBackedAPIKey


class FileBackedAPIKeyRequestAuthenticator(BearerTokenRequestAuthenticator):
    """
    Load a bearer token from a file just in time for the request.
    Perform local checks on the validity of the token and throw
    if we think it will fail.
    """
    def __init__(self, auth_file: FileBackedAPIKey):
        super().__init__(token_body='')
        self._auth_file = auth_file

    def _load(self):
        self._auth_file.lazy_reload()
        self._auth_file.assert_valid()
        self._token_prefix = self._auth_file.bearer_token_prefix()
        self._token_body = self._auth_file.api_key()

    def __call__(self, r):
        self._load()
        super().__call__(r)
        return r
