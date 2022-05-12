from abc import abstractmethod
from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.auth_client import \
    AuthClientConfig, \
    AuthClient
from planet.auth.oidc.api_clients.authorization_api_client import \
    AuthorizationApiClient
from planet.auth.oidc.api_clients.discovery_api_client import \
    DiscoveryApiClient
from planet.auth.oidc.api_clients.introspect_api_client import \
    IntrospectionApiClient
from planet.auth.oidc.api_clients.jwks_api_client import \
    JwksApiClient
from planet.auth.oidc.token_validator import \
    TokenValidator
from planet.auth.oidc.api_clients.revocation_api_client import \
    RevocationApiClient
from planet.auth.oidc.api_clients.token_api_client import \
    TokenApiClient
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential


class OidcAuthClientConfig(AuthClientConfig):

    def __init__(self,
                 auth_server,
                 client_id,
                 default_request_scopes=None,
                 authorization_endpoint=None,
                 introspection_endpoint=None,
                 jwks_endpoint=None,
                 revocation_endpoint=None,
                 token_endpoint=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.auth_server = auth_server
        self.client_id = client_id
        self.default_request_scopes = default_request_scopes
        self.authorization_endpoint = authorization_endpoint
        self.introspection_endpoint = introspection_endpoint
        self.jwks_endpoint = jwks_endpoint
        self.revocation_endpoint = revocation_endpoint
        self.token_endpoint = token_endpoint


class OidcAuthClient(AuthClient):

    def __init__(self, oidc_client_config: OidcAuthClientConfig):
        super().__init__(oidc_client_config)
        self._oidc_client_config = oidc_client_config
        self.__discovery_client = DiscoveryApiClient(
            auth_server=self._oidc_client_config.auth_server)
        self.__token_client = None
        self.__authorization_client = None
        self.__introspection_client = None
        self.__revocation_client = None
        self.__jwks_client = None
        self.__token_validator = None

    def _discovery(self):
        # We know the internals of the discovery client fetch this
        # JIT and caches
        return self.__discovery_client.discovery()

    def _token_validator(self):
        if not self.__token_validator:
            self.__token_validator = TokenValidator(self._jwks_client())
        return self.__token_validator

    def _authorization_client(self):
        if not self.__authorization_client:
            if self._oidc_client_config.authorization_endpoint:
                auth_endpoint = self._oidc_client_config.authorization_endpoint
            else:
                auth_endpoint = self._discovery()['authorization_endpoint']
            self.__authorization_client = AuthorizationApiClient(auth_endpoint)
        return self.__authorization_client

    def _introspection_client(self):
        if not self.__introspection_client:
            if self._oidc_client_config.introspection_endpoint:
                introspection_endpoint = \
                    self._oidc_client_config.introspection_endpoint
            else:
                introspection_endpoint = self._discovery(
                )['introspection_endpoint']
            self.__introspection_client = IntrospectionApiClient(
                introspection_endpoint)
        return self.__introspection_client

    def _jwks_client(self):
        if not self.__jwks_client:
            if self._oidc_client_config.jwks_endpoint:
                jwks_endpoint = self._oidc_client_config.jwks_endpoint
            else:
                jwks_endpoint = self._discovery()['jwks_uri']
            self.__jwks_client = JwksApiClient(jwks_endpoint)
        return self.__jwks_client

    def _revocation_client(self):
        if not self.__revocation_client:
            if self._oidc_client_config.revocation_endpoint:
                revocation_endpoint = \
                    self._oidc_client_config.revocation_endpoint
            else:
                revocation_endpoint = self._discovery()['revocation_endpoint']
            self.__revocation_client = RevocationApiClient(revocation_endpoint)
        return self.__revocation_client

    def _token_client(self):
        if not self.__token_client:
            if self._oidc_client_config.token_endpoint:
                token_endpoint = self._oidc_client_config.token_endpoint
            else:
                token_endpoint = self._discovery()['token_endpoint']
            self.__token_client = TokenApiClient(token_endpoint)
        return self.__token_client

    # Note: I don't really like that auth_client knows about the HTTP-ness,
    #       that's the job of the API client classes to abstract.  It's
    #       difficult to entirely separate these concerns, since the high
    #       level concept of "OIDC client type" imposes itself on some of
    #       the low level protocol interactions.
    @abstractmethod
    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        """
        Some OIDC endpoints require client auth, and how auth is done can
        very depending on how the OIDC provider is configured to handle the
        particular client and the particular flow of the token grant.

        Auth clients implementation classes must implement a method to enrich
        requests with appropriate authentication either by modifying the
        payload, or providing an AuthBase for the request, which will be used
        where needed before sending requests to the authorization servers.

        If no enrichment is needed or appropriate, implementations should
        return the raw payload unmodified, and None for the AuthBase.

        See
        https://developer.okta.com/docs/reference/api/oidc/#client-authentication-methods
        """

    @abstractmethod
    def login(self,
              requested_scopes=None,
              allow_open_browser=True,
              **kwargs) -> FileBackedOidcCredential:
        """
         Obtain tokens from the OIDC auth server using an appropriate login
         flow. concrete subclasses should implement a single login flow.
         Args:
              requested_scopes: a list of strings specifying the scopes to
                  request.
              allow_open_browser: specify whether login is permitted to open
                  a browser window.
          Returns:
              A FileBackedOidcCredential object
        """

    def refresh(self, refresh_token, requested_scopes=None):
        """
        Refresh auth tokens using the provided refresh token
        Args:
            refresh_token: the refresh token to use.
            requested_scopes: a list of strings specifying the scopes to
            request during the token refresh. If not specified, server
            default behavior will apply.
        Returns:
            A FileBackedOidcCredential object
        """
        # Disabled scope fallback for now.
        # The client config default may have more than the user consented to,
        # which will result in a failure.  Introspection could be used, but
        # if this approach is taken, the access token should be inspected.
        # Inspecting refresh tokens shows its full power, whereas inspecting
        # the access token reveals if it was down-scoped for some reason.
        # However, access tokes live a short time, and inspection fails after
        # expiration, whereas refresh tokens may live much longer lives.
        #
        # if not requested_scopes:
        #    requested_scopes = self._oidc_client_config.default_request_scopes
        return FileBackedOidcCredential(self._token_client().get_token_from_refresh(
            self._oidc_client_config.client_id,
            refresh_token,
            requested_scopes))

    def validate_access_token(self, access_token):
        """
        Validate the access token against the OIDC token introspection endpoint
        :param access_token:
        :return:
            The raw validate json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_access_token(
            access_token, self._client_auth_enricher)

    def validate_access_token_local(self, access_token, audience):
        # The client doesn't know resource server's expected audience,
        # so this perhaps doesn't belong in "AuthClient"
        return self._token_validator().validate_token(
            token_str=access_token,
            issuer=self._oidc_client_config.auth_server,
            audience=audience)

    def validate_id_token(self, id_token):
        """
        Validate the ID token against the OIDC token introspection endpoint
        :param id_token:
        :return:
            The raw validate json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_id_token(
            id_token, self._client_auth_enricher)

    def validate_id_token_local(self, id_token):
        """
        Validate the ID token locally. A remote connection may still be made
        to obtain signing keys.
        :param id_token:
        :return:
            Upon success, the validated token claims are returned
        """
        # return self._token_validator().validate_token(
        #    token_str=id_token,
        #    issuer=self._oidc_client_config.auth_server,
        #    audience=self._oidc_client_config.client_id)
        return self._token_validator().validate_id_token(
            token_str=id_token,
            issuer=self._oidc_client_config.auth_server,
            client_id=self._oidc_client_config.client_id)

    def validate_refresh_token(self, refresh_token):
        """
        Validate the refresh token against the OIDC token introspection
        endpoint
        :param refresh_token:
        :return:
            The raw validate json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_refresh_token(
            refresh_token, self._client_auth_enricher)

    def revoke_access_token(self, access_token) -> None:
        """
        Revoke the access token with the OIDC provider.
        :param access_token
        """
        self._revocation_client().revoke_access_token(
            access_token, self._client_auth_enricher)

    def revoke_refresh_token(self, refresh_token) -> None:
        """
        Revoke the refresh token with the OIDC provider.
        :param refresh_token
        """
        self._revocation_client().revoke_refresh_token(
            refresh_token, self._client_auth_enricher)

    def get_scopes(self):
        return self._discovery()['scopes_supported']
