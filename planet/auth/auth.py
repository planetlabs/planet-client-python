from __future__ import annotations  # https://stackoverflow.com/a/33533514
import logging
import os
import pathlib
from typing import Tuple, Union

from planet.cli.constants import \
    DEFAULT_OIDC_AUTH_CLIENT_CONFIG, \
    LEGACY_AUTH_CLIENT_CONFIG
from planet.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_TOKEN_FILE
from planet.auth.auth_client import AuthClient, AuthClientConfig
from planet.auth.request_authenticator import RequestAuthenticator


logger = logging.getLogger(__name__)


class Profile:
    @staticmethod
    def get_profile_file_path(
            filename: str,
            profile: Union[str, None],
            override_path: Union[str, pathlib.PurePath, None]
    ) -> pathlib.Path:
        if override_path:
            return pathlib.Path(override_path)
        if not profile or profile == '' or profile.lower() == 'default':
            return pathlib.Path.home().joinpath(".planet/{}".format(filename))
        else:
            return pathlib.Path.home().joinpath(".planet/{}/{}".format(profile.lower(), filename))


class Auth:
    def __init__(self,
                 auth_client: AuthClient = None,
                 request_authenticator: RequestAuthenticator = None,
                 token_file_path: pathlib.Path = None):
        self._auth_client = auth_client
        self._request_authenticator = request_authenticator
        self._token_file_path = token_file_path
        # self._credential = credential

    def auth_client(self) -> AuthClient:
        return self._auth_client

    def request_authenticator(self) -> RequestAuthenticator:
        return self._request_authenticator

    def token_file_path(self) -> pathlib.Path:
        return self._token_file_path

    @staticmethod
    def _initialize_auth_client(
            profile: str,
            auth_client_config_file: Union[str, pathlib.PurePath]
    ) -> AuthClient:
        if not profile or profile == '' or profile.lower() == 'default':
            logger.debug('Using built-in "default" auth client configuration')
            auth_client = AuthClient.from_config(DEFAULT_OIDC_AUTH_CLIENT_CONFIG)
        elif profile.lower() == 'legacy':
            logger.debug('Using built-in "legacy" auth client configuration')
            auth_client = AuthClient.from_config(LEGACY_AUTH_CLIENT_CONFIG)
        else:
            auth_config_path = Profile.get_profile_file_path('auth_client.json', profile, auth_client_config_file)
            if auth_config_path.exists():
                logger.debug('Using auth client configuration from "{}"'.format(str(auth_config_path)))
                client_config = AuthClientConfig.from_file(auth_client_config_file)
            else:
                logger.debug('Auth configuration file "{}" not found.'
                             ' Using built-in default auth client configuration'
                             .format(str(auth_config_path)))
                client_config = DEFAULT_OIDC_AUTH_CLIENT_CONFIG
            auth_client = AuthClient.from_config(client_config)

        return auth_client

    @staticmethod
    def initialize(
            profile: str = os.getenv(ENV_AUTH_PROFILE),
            auth_client_config_file: Union[str, pathlib.PurePath] = os.getenv(ENV_AUTH_CLIENT_CONFIG_FILE),
            token_file: Union[str, pathlib.PurePath] = os.getenv(ENV_AUTH_TOKEN_FILE)
    ) -> Auth:

        auth_client = Auth._initialize_auth_client(profile, auth_client_config_file)
        token_file_path = Profile.get_profile_file_path('token.json', profile, token_file)
        request_authenticator = auth_client.default_request_authenticator(token_file_path)

        return Auth(auth_client, request_authenticator, token_file_path)