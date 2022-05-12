from __future__ import annotations  # https://stackoverflow.com/a/33533514

from abc import ABC, abstractmethod
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

    def __init__(self, message=None):
        super().__init__(message)


class AuthClientConfig(ABC):
    _typename_map = {}

    def __init__(self, **kwargs):
        if len(kwargs.keys()) > 0:
            # raise AuthClientConfigException(
            # 'Unexpected config arguments in client configuration: {}'
            # .format(', '.join(kwargs.keys())))
            for key in kwargs.keys():
                logger.debug('Ignoring unknown keyword argument: "{}"'.format(
                    str(key)))

    @classmethod
    def _get_typename_map(cls):
        if not cls._typename_map:
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsClientSecretClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsSharedKeyClientConfig
            from planet.auth.oidc.auth_clients.resource_owner_flow import \
                ResourceOwnerClientConfig
            from planet.auth.planet_legacy.auth_client import \
                PlanetLegacyAuthClientConfig
            from planet.auth.static_api_key.auth_client import \
                StaticApiKeyAuthClientConfig

            cls._typename_map = {
                'oidc_auth_code': AuthCodePKCEClientConfig,
                'oidc_client_credentials_secret':
                ClientCredentialsClientSecretClientConfig,
                'oidc_client_credentials_pubkey':
                ClientCredentialsPubKeyClientConfig,
                'oidc_client_credentials_sharedkey':
                ClientCredentialsSharedKeyClientConfig,
                'oidc_resource_owner': ResourceOwnerClientConfig,
                'planet_legacy': PlanetLegacyAuthClientConfig,
                'static_apikey': StaticApiKeyAuthClientConfig
            }

        return cls._typename_map

    @classmethod
    def from_dict(cls, config_data: dict):
        config_data.get('client_type')
        config_type = config_data.get('client_type')
        config_cls = AuthClientConfig._get_typename_map().get(config_type)
        if not config_cls:
            raise AuthClientException(
                'Error: Auth client config type "{}" is not understood by'
                ' the factory.'.format(config_type))
        return config_cls(**config_data)

    @staticmethod
    def from_file(file_path) -> AuthClientConfig:
        # TODO: do we want to make file backing an intrinsic part of the base
        #       class? It would be nice for saving configs, but I don't think
        #       creating a new object for the purpose of writing a config file
        #       is really a use case that is a high priority.
        config_file = FileBackedJsonObject(file_path=file_path)
        config_file.load()
        return AuthClientConfig.from_dict(config_file.data())


class AuthClient(ABC):
    _type_map = {}

    def __init__(self, auth_client_config: AuthClientConfig):
        self._auth_client_config = auth_client_config

    @classmethod
    def _get_type_map(cls):
        if not cls._type_map:
            from planet.auth.oidc.auth_clients.auth_code_flow import \
                AuthCodePKCEAuthClient, \
                AuthCodePKCEClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import \
                ClientCredentialsPubKeyAuthClient, \
                ClientCredentialsPubKeyClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import\
                ClientCredentialsClientSecretAuthClient, \
                ClientCredentialsClientSecretClientConfig
            from planet.auth.oidc.auth_clients.client_credentials_flow import\
                ClientCredentialsSharedKeyAuthClient, \
                ClientCredentialsSharedKeyClientConfig
            from planet.auth.oidc.auth_clients.resource_owner_flow import\
                ResourceOwnerAuthClient, \
                ResourceOwnerClientConfig
            from planet.auth.planet_legacy.auth_client import \
                PlanetLegacyAuthClient, \
                PlanetLegacyAuthClientConfig
            from planet.auth.static_api_key.auth_client import \
                StaticApiKeyAuthClient, \
                StaticApiKeyAuthClientConfig

            cls._type_map = {
                AuthCodePKCEClientConfig: AuthCodePKCEAuthClient,
                ClientCredentialsClientSecretClientConfig:
                ClientCredentialsClientSecretAuthClient,
                ClientCredentialsPubKeyClientConfig:
                ClientCredentialsPubKeyAuthClient,
                ClientCredentialsSharedKeyClientConfig:
                ClientCredentialsSharedKeyAuthClient,
                ResourceOwnerClientConfig: ResourceOwnerAuthClient,
                PlanetLegacyAuthClientConfig: PlanetLegacyAuthClient,
                StaticApiKeyAuthClientConfig: StaticApiKeyAuthClient
            }

        return cls._type_map

    @classmethod
    def from_config(cls, config: AuthClientConfig) -> AuthClient:
        client_cls = AuthClient._get_type_map().get(type(config))
        if not client_cls:
            raise AuthClientException(
                'Error: Auth client config class is not understood by'
                ' the factory.')

        return client_cls(config)

    @abstractmethod
    def login(self, **kwargs) -> Credential:
        """
        Perform a login using the authentication mechanism implemented by the
        AuthClient instance.  The results of a successful login is
        FileBackedJsonObject Credential containing credentials that may be
        used for subsequent service API requests.  How these credentials are
        used for this purpose is outside the scope of either the AuthClient
        or the Credential.  This is the job of a RequestAuthenticator

        :param kwargs:
        :return:
        """

    def refresh(self, refresh_token, requested_scopes):
        raise AuthClientException(
            'Refresh not implemented for the current authentication mechanism')

    def validate_access_token(self, access_token):
        raise AuthClientException(
            'Access token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_id_token(self, id_token):
        raise AuthClientException(
            'ID token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_id_token_local(self, id_token):
        raise AuthClientException(
            'ID token validation is not implemented for the current'
            ' authentication mechanism')

    def validate_refresh_token(self, refresh_token):
        raise AuthClientException(
            'Refresh token validation is not implemented for the current'
            ' authentication mechanism')

    def revoke_access_token(self, access_token):
        raise AuthClientException(
            'Access token revocation is not implemented for the current'
            ' authentication mechanism')

    def revoke_refresh_token(self, refresh_token):
        raise AuthClientException(
            'Refresh token revocation is not implemented for the current'
            ' authentication mechanism')

    def get_scopes(self):
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

        :param credential_file_path:
        :return:
        """
