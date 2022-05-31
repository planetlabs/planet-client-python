from __future__ import annotations  # https://stackoverflow.com/a/33533514

from abc import ABC, abstractmethod
from typing import List
import logging
import pathlib

from planet.auth.auth_exception import AuthException
from planet.auth.credential import Credential
from planet.auth.request_authenticator import RequestAuthenticator
from planet.auth.util import FileBackedJsonObject

logger = logging.getLogger(__name__)


class AuthClientException(AuthException):

    def __init__(self, message=None, inner_exception=None):
        super().__init__(message, inner_exception)


class AuthClientConfigException(AuthClientException):

    def __init__(self, message=None, inner_exception=None):
        super().__init__(message, inner_exception)


class AuthClientConfig(ABC):
    """
    Base class for auth client configuration objects. Each concrete auth
    client type has a dedicated auth client config type help and keep
    the varied configuration needs of different clients on rails.

    The factory methods in the base class accept a dictionary, and will
    return an instance of an appropriate subclass.

    Example:
        ```python
        >>> from planet.auth import AuthClientConfig
        >>> config_dict = {
        ...     "client_type": "oidc_auth_code",
        ...     "auth_server": "https://account.planet.com/oauth2",
        ...     "client_id": "your_client_id",
        ...     "redirect_uri": "https://your_client_redirect_uri",
        ...     "default_request_scopes": [
        ...         "planet",
        ...         "offline_access",
        ...         "openid",
        ...         "profile"]
        ... }
        >>> my_auth_config = AuthClientConfig.from_dict(config_dict)
        >>> # an instance of AuthCodePKCEClientConfig will be created
        ```
    """

    _typename_map = {}
    CLIENT_TYPE_KEY = 'client_type'

    def __init__(self, **kwargs):
        if len(kwargs.keys()) > 0:
            # raise AuthClientConfigException(
            # 'Unexpected config arguments in client configuration: {}'
            # .format(', '.join(kwargs.keys())))
            for key in kwargs.keys():
                if key != AuthClientConfig.CLIENT_TYPE_KEY:
                    logger.debug(
                        'Ignoring unknown keyword argument: "{}"'.format(
                            str(key)))

    @classmethod
    def _get_typename_map(cls):
        if not cls._typename_map:
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEClientConfig
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEWithClientSecretClientConfig
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEWithPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsClientSecretClientConfig
            from planet.auth.oidc.auth_clients.resource_owner_flow import \
                ResourceOwnerClientConfig
            from planet.auth.planet_legacy.auth_client import \
                PlanetLegacyAuthClientConfig
            from planet.auth.static_api_key.auth_client import \
                StaticApiKeyAuthClientConfig
            from planet.auth.none.noop_auth import \
                NoOpAuthClientConfig

            cls._typename_map = {
                'oidc_auth_code': AuthCodePKCEClientConfig,
                'oidc_auth_code_secret':
                AuthCodePKCEWithClientSecretClientConfig,
                'oidc_auth_code_pubkey': AuthCodePKCEWithPubKeyClientConfig,
                'oidc_client_credentials_secret':
                ClientCredentialsClientSecretClientConfig,
                'oidc_client_credentials_pubkey':
                ClientCredentialsPubKeyClientConfig,
                'oidc_resource_owner': ResourceOwnerClientConfig,
                'planet_legacy': PlanetLegacyAuthClientConfig,
                'static_apikey': StaticApiKeyAuthClientConfig,
                'none': NoOpAuthClientConfig
            }

        return cls._typename_map

    @classmethod
    def from_dict(cls, config_data: dict) -> AuthClientConfig:
        """
        Create a AuthClientConfig from a configuration dictionary.
        Returns:
            A concrete auth client config object.
        """
        config_type = config_data.get(cls.CLIENT_TYPE_KEY)
        config_cls = AuthClientConfig._get_typename_map().get(config_type)
        if not config_cls:
            raise AuthClientException(
                'Error: Auth client config type "{}" is not understood by'
                ' the factory.'.format(config_type))
        return config_cls(**config_data)

    @staticmethod
    def from_file(file_path) -> AuthClientConfig:
        """
        Create an AuthClientConfig from a json file that contains a config
        dictionary.
        Returns:
            A concrete auth client config object.
        """
        # TODO: do we want to make file backing an intrinsic part of the base
        #       class? It would be nice for saving configs, but I don't think
        #       creating a new object for the purpose of writing a config file
        #       is really a use case that is a high priority.
        config_file = FileBackedJsonObject(file_path=file_path)
        config_file.load()
        return AuthClientConfig.from_dict(config_file.data())


class AuthClient(ABC):
    """
    Base class for auth clients.  Concrate instances of this base class
    manage the specific of how to authenticate a user and obtain credentials
    that may be used for service APIs.

    The factory methods in the base class accepts a client specific client
    configuraiton type, and will return an instance of an appropriate subclass.

    Example:
        ```python
        >>> from planet.auth import AuthClientConfig, AuthClient
        >>> config_dict = { ... } # See AuthClientConfig
        >>> my_auth_config = AuthClientConfig.from_dict(config_dict)
        >>> my_auth_client = AuthClient.from_config(my_auth_config)
        ```
    """

    _type_map = {}

    def __init__(self, auth_client_config: AuthClientConfig):
        self._auth_client_config = auth_client_config

    @classmethod
    def _get_type_map(cls):
        if not cls._type_map:
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEAuthClient, \
                AuthCodePKCEClientConfig
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEWithClientSecretAuthClient, \
                AuthCodePKCEWithClientSecretClientConfig
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEWithPubKeyAuthClient, \
                AuthCodePKCEWithPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsPubKeyAuthClient, \
                ClientCredentialsPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import\
                ClientCredentialsClientSecretAuthClient, \
                ClientCredentialsClientSecretClientConfig
            from planet.auth.oidc.auth_clients.resource_owner_flow import\
                ResourceOwnerAuthClient, \
                ResourceOwnerClientConfig
            from planet.auth.planet_legacy.auth_client import \
                PlanetLegacyAuthClient, \
                PlanetLegacyAuthClientConfig
            from planet.auth.static_api_key.auth_client import \
                StaticApiKeyAuthClient, \
                StaticApiKeyAuthClientConfig
            from planet.auth.none.noop_auth import \
                NoOpAuthClient, \
                NoOpAuthClientConfig

            cls._type_map = {
                AuthCodePKCEClientConfig: AuthCodePKCEAuthClient,
                AuthCodePKCEWithClientSecretClientConfig:
                AuthCodePKCEWithClientSecretAuthClient,
                AuthCodePKCEWithPubKeyClientConfig:
                AuthCodePKCEWithPubKeyAuthClient,
                ClientCredentialsClientSecretClientConfig:
                ClientCredentialsClientSecretAuthClient,
                ClientCredentialsPubKeyClientConfig:
                ClientCredentialsPubKeyAuthClient,
                ResourceOwnerClientConfig: ResourceOwnerAuthClient,
                PlanetLegacyAuthClientConfig: PlanetLegacyAuthClient,
                StaticApiKeyAuthClientConfig: StaticApiKeyAuthClient,
                NoOpAuthClientConfig: NoOpAuthClient
            }

        return cls._type_map

    @classmethod
    def from_config(cls, config: AuthClientConfig) -> AuthClient:
        """
        Create an AuthClient of an appropriate subtype from the client config.
        Returns:
            An initialized auth client instance.
        """
        client_cls = AuthClient._get_type_map().get(type(config))
        if not client_cls:
            raise AuthClientException(
                'Error: Auth client config class is not understood by'
                ' the factory.')

        return client_cls(config)

    @abstractmethod
    def login(self, **kwargs) -> Credential:
        """
        Perform an initial login using the authentication mechanism
        implemented by the AuthClient instance.  The results of a successful
        login is FileBackedJsonObject Credential containing credentials that
        may be used for subsequent service API requests.  How these
        credentials are used for this purpose is outside the scope of either
        the AuthClient or the Credential.  This is the job of a
        RequestAuthenticator.

        The login command is permitted to be user interactive.  Depending on
        the implementation, this may terminal prompts, or may require the
        use of a web browser.

        Returns:
            Upon successful login, a Credential will be returned. The returned
            value will be in memory only. It is the responsibility of the
            application to save this credential to disk as appropriate using
            the mechanisms built into the Credential type.
        """

    def refresh(self, refresh_token: str,
                requested_scopes: List[str]) -> Credential:
        # TODO: It may be better to accept a Credential as input?
        """
        Obtain a refreshed credential using the supplied refresh token.
        This method will be implemented by concrete AuthClients that
        implement a particular OAuth flow.
        Parameters:
            refresh_token: Refresh token
            requested_scopes: Scopes to request in the access token
        Returns:
            Upon success, a fresh Credential will be returned. As with
            login(), this credential will not have been persisted to storage.
            This is the responsibility of the application.
        """
        raise AuthClientException(
            'Refresh not implemented for the current authentication mechanism')

    def validate_access_token(self, access_token: str):
        """
        Validate an access token with the authorization server.
        Parameters:
            access_token: Access token to validate
        Returns:
            Returns a dictionary of validated token claims
        """
        raise AuthClientException(
            'Access token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_access_token_local(self,
                                    access_token: str,
                                    required_audience: str):
        """
        Validate an access token locally. The authorization server may still
        may called to obtain signing keys for validation.  Signing keys will
        be cached for future use.  While tokens may be requested and have
        multiple audiences, validation currently only supports checking
        for a single audience.
        Parameters:
            access_token: Access token to validate
            required_audience:
        Returns:
            Returns a dictionary of validated token claims
        """
        raise AuthClientException(
            'Access token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_id_token(self, id_token: str):
        """
        Validate an ID token with the authorization server.
        Parameters:
            id_token: ID token to validate
        Returns:
            Returns a dictionary of validated token claims
        """
        raise AuthClientException(
            'ID token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_id_token_local(self, id_token: str):
        """
        Validate an ID token locally. The authorization server may still be
        called to obtain signing keys for validation.  Signing keys will be
        cached for future use.
        Parameters:
            id_token: ID token to validate
        Returns:
            Returns a dictionary of validated token claims
        """
        raise AuthClientException(
            'ID token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_refresh_token(self, refresh_token: str):
        """
        Validate a refresh token with the authorization server.
        Parameters:
            refresh_token: Refresh token to validate
        Returns:
        """
        raise AuthClientException(
            'Refresh token validation is not implemented for the current'
            ' authentication mechanism')

    def revoke_access_token(self, access_token: str):
        """
        Revoke an access token with the authorization server.
        Parameters:
            access_token: Access token to revoke.
        """
        raise AuthClientException(
            'Access token revocation is not implemented for the current'
            ' authentication mechanism')

    def revoke_refresh_token(self, refresh_token: str):
        """
        Revoke a refresh token with the authorization server.
        Parameters:
            refresh_token: Access token to revoke.
        """
        raise AuthClientException(
            'Refresh token revocation is not implemented for the current'
            ' authentication mechanism')

    def get_scopes(self):
        """
        Query the authorization server for a list of scopes.
        Returns:
            Returns a list of scopes that may be requested during a call
            to login or refresh
        """
        raise AuthClientException(
            'Listing scopes is not implemented for the current'
            ' authentication mechanism.')

    @abstractmethod
    def default_request_authenticator(
            self, credential_file_path: pathlib.Path) -> RequestAuthenticator:
        """
        Return an instance of the default request authenticator to use for
        the specific AuthClient type and configured to use the provided
        credential file for persistence.

        It's not automatic that the default is always the right choice.
        Some authenticators may initiate logins, which may be interactive
        or not depending on the specifics of the AuthClient configuration
        and implementation type. Whether or not interactivity can be
        tolerated depends on the specifics of the surrounding application.

        In the simplest cases, there really is no relationship between
        the AuthClient and the request authenticator (see static key
        implementations). This relationship emerges when the mechanisms
        of an AuthClient requires frequent refreshing of the Credential.
        In these cases, it is convenient for the RequestAuthenticator
        to also have an AuthClient that is capable of performing this
        refresh transparently as needed.

        AuthClient implementors should favor defaults that do not require
        user interaction after an initial Credential has been obtained from
        an initial call to login()

        Parameters:
            credential_file_path: Path to the credential file that should be
            used.
        Returns:
            Returns an instance of the default request authenticator class
            to use for Credentials of the type obtained by the AuthClient.
        """
