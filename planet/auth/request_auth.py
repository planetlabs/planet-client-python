import logging
import requests.auth

logger = logging.getLogger(__name__)


class BearerTokenAuth(requests.auth.AuthBase):
    """
    Decorate a http request with a bearer auth token.
    """
    def __init__(self, token_body, token_prefix='Bearer', auth_header='Authorization'):
        super().__init__()
        self._token_prefix = token_prefix
        self._token_body = token_body
        self._auth_header = auth_header

    def __call__(self, r):
        if self._token_prefix:
            # Should we make the space part of the prefix?  What if someone wants no space?
            r.headers[self._auth_header] = self._token_prefix + ' ' + self._token_body
        else:
            r.headers[self._auth_header] = self._token_body
        return r
