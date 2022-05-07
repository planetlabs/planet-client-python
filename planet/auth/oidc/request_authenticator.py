import logging
import jwt
import time

from planet.auth.request_authenticator import RequestAuthenticator
from planet.auth.oidc.auth_client import OidcAuthClient
from planet.auth.oidc.oidc_token import FileBackedOidcToken

logger = logging.getLogger(__name__)


# Note: Auth client can be passed override scopes for token refresh, but we
#       haven't plumbed our auth helpers to do this. This is probably an
#       acceptable limitation for this use case.
class RefreshingOidcTokenRequestAuthenticator(RequestAuthenticator):
    """
    Decorate a http request with a bearer auth token. Automatically initiate a
    refresh request if we know the access token to be close to expiration.

    This class assumes access tokens are JWTs and can be locally inspected,
    which OIDC and OAuth do not require.  JWT access tokens that comply with
    RFC 9068 can be checked for expiration timing without hitting the network
    token introspection endpoint.
    """

    #  TODO: fix naming - token_file -> credential_file (fix class names too)
    def __init__(self,
                 token_file: FileBackedOidcToken,
                 auth_client: OidcAuthClient = None):
        super().__init__(token_body='')
        self._token = token_file
        self._auth_client = auth_client
        self._refresh_at = 0

    def _load(self):
        # Absolutely not appropriate to not verify the signature in a token
        # validation context (e.g. server side auth of a client). Here we
        # know that's not what we are doing. This is a client helper class
        # for clients who will be presenting tokens to such a server.  We
        # are inspecting ourselves, not verifying for trust purposes.
        # We are not expected to be the audience.
        self._token.load()
        # self._token.assert_valid()
        access_token_str = self._token.access_token()
        unverified_decoded_atoken = jwt.decode(
            access_token_str, options={"verify_signature": False})
        iat = unverified_decoded_atoken.get('iat') or 0
        exp = unverified_decoded_atoken.get('exp') or 0
        # refresh at the 3/4 life
        self._refresh_at = int(iat + (3 * (exp - iat) / 4))
        self._token_body = access_token_str

    def _refresh(self):
        if self._auth_client:
            new_token = self._auth_client.refresh(self._token.refresh_token())
            new_token.set_path(self._token.path())
            new_token.save()
            self._token = new_token
            self._load()

    def pre_request_hook(self):
        if int(time.time()) > self._refresh_at:
            try:
                # Reload the file before refreshing. Another process might
                # have done it for us, and save us the network call.  Also,
                # if refresh tokens are configured to be one time use, we
                # want a fresh refresh token. Stale refresh tokens are
                # invalid in this case.
                self._load()
                if int(time.time()) > self._refresh_at:
                    self._refresh()
            except Exception as e:
                # we continue with the old auth token to try and be resilient.
                # Refresh failures could be transient.
                logger.warning(
                    "Error refreshing auth token. Continuing with old auth"
                    " token. Refresh error: " + str(e))

        super().pre_request_hook()


class RefreshOrReloginOidcTokenRequestAuthenticator(
        RefreshingOidcTokenRequestAuthenticator):
    """
    Decorate a http request with a bearer auth token. Automatically initiate
    a refresh request using the refresh token if we know the access token to
    be close to expiration. If we do not have a refresh token, then fall back
    to re-initiating a login.  Sometimes (like with client credential flow),
    refresh tokens may not be available and we might want to login rather
    than refresh.  It is not an automatic choice to fall back to login when
    refresh is not available, since for some auth client configurations login
    is interactive, and would not be appropriate for headless use cases.
    Refresh should always be silent.
    """

    def __init__(self,
                 token_file: FileBackedOidcToken,
                 auth_client: OidcAuthClient = None):
        super().__init__(token_file=token_file, auth_client=auth_client)

    def _refresh(self):
        if self._auth_client:
            if self._token.refresh_token():
                new_token = self._auth_client.refresh(
                    self._token.refresh_token())
            else:
                new_token = self._auth_client.login()

            new_token.set_path(self._token.path())
            new_token.save()
            self._token = new_token
            self._load()
