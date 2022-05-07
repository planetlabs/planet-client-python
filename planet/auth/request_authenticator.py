import logging
from abc import abstractmethod

import httpx
import requests.auth

logger = logging.getLogger(__name__)


class RequestAuthenticator(requests.auth.AuthBase, httpx.Auth):
    """
    Decorate a http request with a bearer auth token.
    """

    def __init__(self,
                 token_body,
                 token_prefix='Bearer',
                 auth_header='Authorization'):
        super().__init__()
        self._token_prefix = token_prefix
        self._token_body = token_body
        self._auth_header = auth_header

    @abstractmethod
    def pre_request_hook(self):
        """
        Hook that will be called immediately prior to making an HTTP request
        so that implementing classes may make preparations.  Derived
        classes are expected to populate the member fields _token_prefix,
        _token_body, and _auth_header with values that are appropriate to
        the the specific implementation.  These will then be used during
        subsequent HTTP request to authenticate the connection using
        a beater token authorization HTTP header.

        Implementers may make external network calls as required to perform
        necessary tasks such as refreshing access tokens.

        Implementations should not require user interaction by default. If
        an authentication mechanism will require user interaction, this
        should be an explicit decision that is left to the application
        using the RequestAuthenticator to control.
        """

    def _build_auth_header_payload(self):
        if self._token_prefix:
            # Should we make the space part of the prefix?  What if someone
            # wants no space?
            return self._token_prefix + ' ' + self._token_body
        else:
            return self._token_body

    def __call__(self, r):
        """
        Decorate a "requests" library based request with authentication
        """
        self.pre_request_hook()
        if self._token_body:
            r.headers[self._auth_header] = self._build_auth_header_payload()
        return r

    def auth_flow(self, r: httpx._models.Request):
        """
        Decorate a "httpx" library based request with authentication
        """
        self.pre_request_hook()
        if self._token_body:
            r.headers[self._auth_header] = self._build_auth_header_payload()
        yield r


class SimpleInMemoryRequestAuthenticator(RequestAuthenticator):

    def pre_request_hook(self):
        pass
