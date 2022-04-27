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
        so that implementing classes may make preparations
        """
        pass

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
        r.headers[self._auth_header] = self._build_auth_header_payload()
        return r

    def auth_flow(self, r: httpx._models.Request):
        """
        Decorate a "httpx" library based request with authentication
        """
        self.pre_request_hook()
        r.headers[self._auth_header] = self._build_auth_header_payload()
        yield r
