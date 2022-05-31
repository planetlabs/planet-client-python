from __future__ import annotations  # https://stackoverflow.com/a/33533514

import logging
import os
import pathlib
from typing import Union

from planet.auth.auth_exception import AuthException
from planet.auth.profile import Profile
from planet.auth.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_TOKEN_FILE, \
    DEFAULT_AUTH_CLIENT_CONFIG_DICT, \
    LEGACY_AUTH_CLIENT_CONFIG_DICT, \
    NOOP_AUTH_CLIENT_CONFIG_DICT, \
    TOKEN_FILE_SOPS, \
    TOKEN_FILE_PLAIN, \
    AUTH_CONFIG_FILE_PLAIN, \
    AUTH_CONFIG_FILE_SOPS

from planet.auth.auth_client import AuthClient, AuthClientConfig
from planet.auth.request_authenticator import RequestAuthenticator

logger = logging.getLogger(__name__)


class Auth:
    """A container class for initializing and grouping a working set of
    authentication objects.  See
    [planet.auth.Auth.initialize][planet.auth.Auth.initialize] for user
    friendly initialization.

    Example:
        ```python
        >>> from planet.auth import Auth
        >>> from planet import Session
        >>>
        >>> my_auth = Auth.initialize()
        >>> async with Session(auth=my_auth) as sess:
                # Application code follows
                ...
        ```
     """

    def __init__(self,
                 auth_client: AuthClient = None,
                 request_authenticator: RequestAuthenticator = None,
                 token_file_path: pathlib.Path = None):
        '''
        Create a new auth container object with the specified auth components.
        See [initialize][planet.auth.Auth.initialize] for user friendly
        construction.
        '''
        self._auth_client = auth_client
        self._request_authenticator = request_authenticator
        self._token_file_path = token_file_path
        # self._credential = credential

    def auth_client(self) -> AuthClient:
        '''
        Get the currently configured auth client.
        Returns:
            The current AuthClient instance.
        '''
        return self._auth_client

    def request_authenticator(self) -> RequestAuthenticator:
        '''
        Get the current request authenticator.
        Returns:
            The current RequestAuthenticator instance.
        '''
        return self._request_authenticator

    def token_file_path(self) -> pathlib.Path:
        '''
        Get the path to the current credentials file.
        Returns:
            returns the path to the current credentials file.
        '''
        return self._token_file_path

    @staticmethod
    def _initialize_auth_client(
        profile: str,
        auth_client_config_file_override: Union[str, pathlib.PurePath]
    ) -> AuthClient:
        if Profile.profile_name_is_default(profile):
            # TODO: New feature (maybe?) allow someone to override the
            #       default for their environment?
            logger.debug(
                'Using built-in "{}" auth client configuration'.format(
                    Profile.BUILTIN_PROFILE_NAME_DEFAULT))
            client_config = AuthClientConfig.from_dict(
                DEFAULT_AUTH_CLIENT_CONFIG_DICT)
        elif Profile.profile_name_is_legacy(profile):
            logger.debug(
                'Using built-in "{}" auth client configuration'.format(
                    Profile.BUILTIN_PROFILE_NAME_LEGACY))
            client_config = AuthClientConfig.from_dict(
                LEGACY_AUTH_CLIENT_CONFIG_DICT)
        elif Profile.profile_name_is_none(profile):
            logger.debug(
                'Using built-in "{}" auth client configuration'.format(
                    Profile.BUILTIN_PROFILE_NAME_NONE))
            client_config = AuthClientConfig.from_dict(
                NOOP_AUTH_CLIENT_CONFIG_DICT)
        else:
            auth_config_path = Profile.get_profile_file_path_with_priority(
                filenames=[AUTH_CONFIG_FILE_SOPS, AUTH_CONFIG_FILE_PLAIN],
                profile=profile,
                override_path=auth_client_config_file_override)
            if auth_config_path.exists():
                logger.debug(
                    'Using auth client configuration from "{}"'.format(
                        str(auth_config_path)))
                client_config = AuthClientConfig.from_file(
                    auth_client_config_file_override)
            else:
                raise AuthException(
                    'Auth configuration file "{}" not found.'.format(
                        str(auth_config_path)))
            # The fallback might be nice for managing multiple user
            # profiles with the CLI or the like, but this fallback behaves
            # poorly when you are working programmatically and expect it
            # to fail.
            #     logger.debug(
            #         'Auth configuration file "{}" not found.'
            #         ' Using built-in default auth client configuration'
            #         .format(str(auth_config_path)))
            #     client_config = AuthClientConfig.from_dict(
            #         DEFAULT_AUTH_CLIENT_CONFIG_DICT)

        return AuthClient.from_config(client_config)

    @staticmethod
    def _initialize_token_file_path(profile: str,
                                    token_file_override) -> pathlib.Path:
        return Profile.get_profile_file_path_with_priority(
            filenames=[TOKEN_FILE_SOPS, TOKEN_FILE_PLAIN],
            profile=profile,
            override_path=token_file_override)

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
        '''
        Construct and initialize a working set of authentication primitives,
        returning them in a new container object.
        Parameters:
            profile: The name of the selected auth profile to initialize. The
                default value will be taken from the environment variable
                PL_AUTH_PROFILE. If this is not set, the built in default
                auth profile will be used.
            auth_client_config_file: The path to an
                [AuthClientConfig][planet.auth.AuthClientConfig] file. If
                not set, the default will be set from the environment variable
                PL_AUTH_CLIENT_CONFIG_FILE.  If this is also not set, the
                profile directory will be searched for the auth client config
                file.  The recommended setting is to leave and the environment
                variable unset, and use the default value.
            token_file: The path to a
                [Credential][planet.auth.Credential] file. If
                not set, the default will be set from the environment variable
                PL_AUTH_TOKEN_FILE.  If this is also not set, the
                profile directory will be searched for the credential
                file.  The recommended setting is to leave and the environment
                variable unset, and use the default value.
        Returns:
            Returns an initialized Auth instance.
        '''
        # TODO: we should have some handling of legacy environment variables
        #       understood by SDK v1: PL_API_KEY
        auth_client = Auth._initialize_auth_client(profile,
                                                   auth_client_config_file)
        token_file_path = Auth._initialize_token_file_path(profile, token_file)
        request_authenticator = Auth._initialize_request_authenticator(
            profile, auth_client, token_file_path)

        return Auth(auth_client, request_authenticator, token_file_path)
