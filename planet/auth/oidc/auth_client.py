from abc import abstractmethod
import cryptography.hazmat.primitives.serialization as crypto_serialization
from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.auth_client import \
    AuthClientConfig, \
    AuthClient, \
    AuthClientConfigException
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
                 default_request_audiences=None,
                 client_secret=None,
                 client_privkey=None,
                 client_privkey_file=None,
                 client_privkey_password=None,
                 issuer=None,
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
        self.default_request_audiences = default_request_audiences
        self.client_secret = client_secret

        self._private_key_data = None
        self.client_privkey_file = client_privkey_file

        if client_privkey and type(client_privkey) is str:
            self.client_privkey = client_privkey.encode()
        else:
            self.client_privkey = client_privkey

        if client_privkey_password and type(client_privkey_password) is str:
            self.client_privkey_password = client_privkey_password.encode()
        else:
            self.client_privkey_password = client_privkey_password

        self.issuer = issuer
        self.authorization_endpoint = authorization_endpoint
        self.introspection_endpoint = introspection_endpoint
        self.jwks_endpoint = jwks_endpoint
        self.revocation_endpoint = revocation_endpoint
        self.token_endpoint = token_endpoint

    # Recast is to catches bad passwords. Too broad? # noqa
    @AuthClientConfigException.recast(TypeError, ValueError)
    def _load_private_key(self):
        # TODO: also handle loading of JWK keys? Fork based on filename
        #       or detect?
        # import jwt
        # priv_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))

        if self.client_privkey:
            priv_key = crypto_serialization.load_pem_private_key(
                self.client_privkey, password=self.client_privkey_password)
            if not priv_key:
                raise AuthClientConfigException(
                    'Unable to load private key literal from configuration')
        else:
            if not self.client_privkey_file:
                raise AuthClientConfigException(
                    'Private key must be configured for public key auth'
                    ' client.')
            with open(self.client_privkey_file, "rb") as key_file:
                priv_key = crypto_serialization.load_pem_private_key(
                    key_file.read(), password=self.client_privkey_password)
                if not priv_key:
                    raise AuthClientConfigException(
                        'Unable to load private key from file "{}"'.format(
                            self.client_privkey_file))
        self._private_key_data = priv_key

    def private_key_data(self):
        # TODO: handle key refresh if the file has changed?
        if not self._private_key_data:
            self._load_private_key()
        return self._private_key_data


class OidcAuthClient(AuthClient):
    """
    Base class for AuthClient implementations that implement an OAuth/OIDC
    authentication flow.
    """

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
        self.__issuer = None

    def _discovery(self):
        # We know the internals of the discovery client fetch this
        # JIT and caches
        # TODO: this does OIDC discovery.  Should we fall back to OAuth2
        #  discovery?  This comes down to .well-known/openid-configuration
        #  vs .well-known/oauth-authorization-server
        return self.__discovery_client.discovery()

    def _issuer(self):
        # Issuer is normally expected to be the same as the auth server.
        # we handle them separately to allow discovery under the auth
        # server url to set the issuer string value used in validation.
        # I can't see much use for this other than deployments where
        # proxy redirects may be in play. In such cases, a proxy may own
        # a public "auth server" URL that routes to particular instances,
        # and there is an expectation that "issuer" (used for token
        # validation) may deviate from the URL used to locate the auth server.
        if not self.__issuer:
            if self._oidc_client_config.issuer:
                self.__issuer = self._oidc_client_config.issuer
            else:
                self.__issuer = self._discovery()['issuer']
                # TODO: should we fall back to the "auth server" if
                #  discovery fails?  In the wild we've seen oauth servers
                #  that lack discovery endpoints, and it would be bad
                #  user experience to force users to provide both
                #  an auth server and an issuer.
        return self.__issuer

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
              requested_audiences=None,
              allow_open_browser=True,
              **kwargs) -> FileBackedOidcCredential:
        """
         Obtain tokens from the OIDC auth server using an appropriate login
         flow. concrete subclasses should implement a single OAuth login flow.
         Args:
              requested_scopes: a list of strings specifying the scopes to
                  request.
              requested_audiences: a list of strings specifying the audiences
                  to request.
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
        return FileBackedOidcCredential(
            self._token_client().get_token_from_refresh(
                self._oidc_client_config.client_id,
                refresh_token,
                requested_scopes))

    def validate_access_token(self, access_token):
        """
        Validate the access token against the OIDC token introspection endpoint
        Parameters:
            access_token: The access token to validate
        Returns:
            The raw validate json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_access_token(
            access_token, self._client_auth_enricher)

    def validate_access_token_local(self, access_token, required_audience):
        # FIXME: A little bit of a mis-match. Audience is a parameter on
        #   local validation, but not server. It's vital information for
        #   performing a local validation, but not an option for server
        #   validation.
        # FIXME: There is also the question of the plurality.  Tokens
        #   may have multiple audiences. When someone requests a token
        #   with multiple audiences, the expectation during login is that
        #   the result has multiple audiences.  However, the underlying
        #   behavior of the jwt.decode() validation appears to be satisfied
        #   if the token under validation has any one of the provided
        #   audiences.  It does not check that all of the provided
        #   audiences are present.
        if not required_audience:
            required_audience = \
                self._oidc_client_config.default_request_audiences

        return self._token_validator().validate_token(
            token_str=access_token,
            issuer=self._issuer(),
            audience=required_audience)

    def validate_id_token(self, id_token):
        """
        Validate the ID token against the OIDC token introspection endpoint
        Parameters:
            id_token: ID token to validate
        Returns:
            The raw validated json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_id_token(
            id_token, self._client_auth_enricher)

    def validate_id_token_local(self, id_token):
        """
        Validate the ID token locally. A remote connection may still be made
        to obtain signing keys.
        Parameters:
            id_token: ID token to validate
        Returns:
            Upon success, the validated token claims are returned
        """
        # return self._token_validator().validate_token(
        #    token_str=id_token,
        #    issuer=self._issuer(),
        #    audience=self._oidc_client_config.client_id)
        return self._token_validator().validate_id_token(
            token_str=id_token,
            issuer=self._issuer(),
            client_id=self._oidc_client_config.client_id)

    def validate_refresh_token(self, refresh_token):
        """
        Validate the refresh token against the OIDC token introspection
        endpoint
        Parameters:
            refresh_token: Refresh token to validate
        Returns:
            The raw validate json payload
            TODO: object model this as a IntrospectionResult, like we do
                  tokens?
        """
        return self._introspection_client().validate_refresh_token(
            refresh_token, self._client_auth_enricher)

    def revoke_access_token(self, access_token) -> None:
        """
        Revoke the access token with the OIDC provider.
        Parameters:
            access_token: The access token to revoke
        """
        self._revocation_client().revoke_access_token(
            access_token, self._client_auth_enricher)

    def revoke_refresh_token(self, refresh_token) -> None:
        """
        Revoke the refresh token with the OIDC provider.
        Parameters:
            refresh_token: The refresh token to revoke
        """
        self._revocation_client().revoke_refresh_token(
            refresh_token, self._client_auth_enricher)

    def get_scopes(self):
        """
        Query the authorization server for a list of scopes.
        Returns:
            Returns a list of scopes that may be requested during a call
            to login or refresh
        """
        return self._discovery()['scopes_supported']
