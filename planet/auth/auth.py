from __future__ import annotations  # https://stackoverflow.com/a/33533514

import logging
import os
import pathlib
from typing import Union

from planet.auth.profile import Profile
from planet.auth.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_TOKEN_FILE, \
    SDK_OIDC_AUTH_CLIENT_CONFIG_DICT, \
    LEGACY_AUTH_CLIENT_CONFIG_DICT

from planet.auth.auth_client import AuthClient, AuthClientConfig
from planet.auth.request_authenticator import \
    RequestAuthenticator, \
    SimpleInMemoryRequestAuthenticator

logger = logging.getLogger(__name__)


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
            auth_client_config_file: Union[str,
                                           pathlib.PurePath]) -> AuthClient:
        if Profile.profile_name_is_default(profile):
            logger.debug(
                'Using built-in "{}" auth client configuration'.format(
                    Profile.BUILTIN_PROFILE_NAME_DEFAULT))
            client_config = AuthClientConfig.from_dict(
                SDK_OIDC_AUTH_CLIENT_CONFIG_DICT)
        elif Profile.profile_name_is_legacy(profile):
            logger.debug(
                'Using built-in "{}" auth client configuration'.format(
                    Profile.BUILTIN_PROFILE_NAME_LEGACY))
            client_config = AuthClientConfig.from_dict(
                LEGACY_AUTH_CLIENT_CONFIG_DICT)
        else:
            auth_config_path = Profile.get_profile_file_path(
                'auth_client.json', profile, auth_client_config_file)
            if auth_config_path.exists():
                logger.debug(
                    'Using auth client configuration from "{}"'.format(
                        str(auth_config_path)))
                client_config = AuthClientConfig.from_file(
                    auth_client_config_file)
            else:
                logger.debug(
                    'Auth configuration file "{}" not found.'
                    ' Using built-in default auth client configuration'.format(
                        str(auth_config_path)))
                client_config = AuthClientConfig.from_dict(
                    SDK_OIDC_AUTH_CLIENT_CONFIG_DICT)

        return AuthClient.from_config(client_config)

    @staticmethod
    def _initialize_token_file_path(profile: str,
                                    token_file_override) -> pathlib.Path:
        return Profile.get_profile_file_path('token.json',
                                             profile,
                                             token_file_override)

    @staticmethod
    def _initialize_request_authenticator(
            profile: str, auth_client: AuthClient,
            token_file_path: pathlib.Path) -> RequestAuthenticator:
        return auth_client.default_request_authenticator(token_file_path)

    @staticmethod
    def initialize(profile: str = os.getenv(ENV_AUTH_PROFILE),
                   auth_client_config_file: Union[str, pathlib.PurePath] = os.
                   getenv(ENV_AUTH_CLIENT_CONFIG_FILE),
                   token_file: Union[str, pathlib.PurePath] = os.getenv(
                       ENV_AUTH_TOKEN_FILE)) -> Auth:
        # TODO: we should have some handling of legacy environment variables
        #       understood by SDK v1: PL_API_KEY
        if Profile.profile_name_is_none(profile):
            auth_client = None
            token_file_path = None
            # TODO: can I set this to None?
            request_authenticator = SimpleInMemoryRequestAuthenticator(
                token_body=None)
        else:
            auth_client = Auth._initialize_auth_client(
                profile, auth_client_config_file)
            token_file_path = Auth._initialize_token_file_path(
                profile, token_file)
            request_authenticator = Auth._initialize_request_authenticator(
                profile, auth_client, token_file_path)

        return Auth(auth_client, request_authenticator, token_file_path)
