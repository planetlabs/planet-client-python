from __future__ import annotations  # https://stackoverflow.com/a/33533514

from abc import ABC, abstractmethod
import logging

from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObject


logger = logging.getLogger(__name__)


class AuthClientException(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class AuthClientConfigException(AuthClientException):
    def __init__(self, message=None):
        super().__init__(message)


class AuthClientConfig(ABC):
    def __init__(self, **kwargs):
        if len(kwargs.keys()) > 0:
            # raise AuthClientConfigException('Unexpected config arguments in client configuration: {}'
            #                                .format(', '.join(kwargs.keys())))
            for key in kwargs.keys():
                logger.debug('Ignoring unknown keyword argument: "{}"'.format(str(key)))

    @staticmethod
    def _typename_map():
        # TODO: make data static rather than rebuild every invocation.
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

        typename_map = {
            'oidc_auth_code': AuthCodePKCEClientConfig,
            'oidc_client_credentials_secret': ClientCredentialsClientSecretClientConfig,
            'oidc_client_credentials_pubkey': ClientCredentialsPubKeyClientConfig,
            'oidc_client_credentials_sharedkey': ClientCredentialsSharedKeyClientConfig,
            'oidc_resource_owner': ResourceOwnerClientConfig,
            'planet_legacy': PlanetLegacyAuthClientConfig
            # TODO:
            #  'static_apikey': StaticApiKeyAuthClientConfig

        }
        return typename_map

    @staticmethod
    def from_file(file_path) -> AuthClientConfig:
        # TODO: do we want to make file backing an intrinsic part of the base class?
        #       It would be nice for saving configs, but I don't think creating a new
        #       object for the purpose of writing a config file is really a use case that
        #       is a high priority.
        config_file = FileBackedJsonObject(file_path=file_path)
        config_file.load()
        config_file.data().get('client_type')
        config_type = config_file.data().get('client_type')
        cls = AuthClientConfig._typename_map().get(config_type)
        if not cls:
            raise AuthClientException('Error: Auth client config type "{}" is not understood by the factory.'
                                      .format(config_type))

        return cls(**config_file.data())


class AuthClient(ABC):
    def __init__(self, auth_client_config: AuthClientConfig):
        self._auth_client_config = auth_client_config

    @staticmethod
    def _type_map():
        # TODO: make data static rather than rebuild every invocation.
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
            PlanetLagacyAuthClient, \
            PlanetLegacyAuthClientConfig

        type_map = {
            AuthCodePKCEClientConfig: AuthCodePKCEAuthClient,
            ClientCredentialsClientSecretClientConfig: ClientCredentialsClientSecretAuthClient,
            ClientCredentialsPubKeyClientConfig: ClientCredentialsPubKeyAuthClient,
            ClientCredentialsSharedKeyClientConfig: ClientCredentialsSharedKeyAuthClient,
            ResourceOwnerClientConfig: ResourceOwnerAuthClient,
            PlanetLegacyAuthClientConfig: PlanetLagacyAuthClient
        }
        return type_map

    @staticmethod
    def from_config(config: AuthClientConfig) -> AuthClient:
        cls = AuthClient._type_map().get(type(config))
        if not cls:
            raise AuthClientException('Error: Auth client config class is not understood by the factory.')

        return cls(config)

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
        pass
