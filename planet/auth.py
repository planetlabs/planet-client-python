# Copyright 2020 Planet Labs, Inc.
# Copyright 2022, 2024, 2025 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Manage authentication with Planet APIs"""
from __future__ import annotations  # https://stackoverflow.com/a/33533514
import abc
import os
import pathlib
import typing
import warnings
import httpx
from typing import List

import planet_auth
import planet_auth_utils

from planet_auth import ObjectStorageProvider

from .constants import SECRET_FILE_PATH
from .auth_builtins import _ProductionEnv, _OIDC_AUTH_CLIENT_CONFIG__USER_SKEL, _OIDC_AUTH_CLIENT_CONFIG__M2M_SKEL
from .exceptions import PlanetError


class AuthType(abc.ABC, httpx.Auth):

    @abc.abstractmethod
    def user_login(
        self,
        allow_open_browser: typing.Optional[bool] = False,
        allow_tty_prompt: typing.Optional[bool] = False,
    ):
        """
        Perform an interactive login.  User interaction will be via the TTY
        and/or a local web browser, with the details dependent on the
        client auth configuration.

        :param allow_open_browser:
        :param allow_tty_prompt:
        """

    @abc.abstractmethod
    def device_user_login_initiate(self) -> dict:
        """
        Initiate a user login that uses the OAuth2 Device Code Flow for applications
        that cannot operate a browser locally.  The returned dictionary should be used
        to prompt the user to complete the process, and will conform to RFC 8628.
        """

    @abc.abstractmethod
    def device_user_login_complete(self, login_initialization_info: dict):
        """
        Complete a user login that uses the OAuth2 Device Code Flow for applications
        that was initiated by a call to `device_user_login_initiate()`.  The structure
        that was returned from `device_user_login_initiate()` should be passed
        to this function unaltered after it has been used to prompt the user.
        """

    @abc.abstractmethod
    def is_initialized(self) -> bool:
        """
        Check whether the user session has been initialized.  For OAuth2
        user based sessions, this means that a login has been performed
        or saved login session data has been located.  For M2M and API Key
        sessions, this should be true if keys or secrets have been
        properly configured.
        """


class Auth(metaclass=abc.ABCMeta):
    """
    Handle authentication information for use with Planet APIs.
    Static constructor methods should be used to create an auth context
    that can be used by Planet API client modules to authenticate
    requests made to the Planet service.
    """

    @staticmethod
    def _normalize_profile_name(profile_name):
        if not profile_name:
            raise ValueError("Profile name must be set")
        if profile_name.find(os.sep) != -1:
            raise ValueError(f"Profile names cannot contain '{os.sep}'")
        return profile_name.lower()

    @staticmethod
    def from_user_default_session() -> AuthType:
        """
        Create authentication from user defaults.

        This method should be used when an application wants to defer
        auth profile management to the user and the `planet auth` CLI
        command entirely.

        Users may use the `planet auth login` command to initialize
        and manage sessions.

        Defaults take into account environment variables (highest priority),
        user configuration saved to `~/.planet.json` and `~/.planet/
        (next priority), and built-in defaults (lowest priority).

        This method does not support the use a custom storage provider.
        The session must be initialized entirely in memory (e.g. through
        environment variables), or from on disk CLI managed settings.

        Environment Variables:
            PL_AUTH_CLIENT_ID: Specify an OAuth2 M2M client ID
            PL_AUTH_CLIENT_SECRET: Specify an OAuth2 M2M client secret
            PL_AUTH_API_KEY: Specify a legacy Planet API key
            PL_AUTH_PROFILE: Specify a custom planet_auth library auth
                client profile (Advanced use cases)
        """
        return _PLAuthLibAuth(plauth=planet_auth_utils.PlanetAuthFactory.
                              initialize_auth_client_context())

    @staticmethod
    def from_profile(profile_name: str) -> AuthType:
        """
        Create authentication for a user whose initialized login information
        has been saved to `~/.planet.json` and `~/.planet/`.

        A user should perform a login to initialize this session out-of-band
        using the command `planet auth login`.

        To initialize this session programmatically without the CLI,
        you must complete an OAuth2 user login flow with one of the login
        methods.

        This method does not support the use a custom storage provider.
        """
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_profile_opt=profile_name)
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    # TODO: add support for confidential clients
    @staticmethod
    def from_oauth_user_auth_code(
        client_id: str,
        callback_url: str,
        requested_scopes: typing.Optional[List[str]] = None,
        save_state_to_storage: bool = True,
        profile_name: typing.Optional[str] = None,
        storage_provider: typing.Optional[ObjectStorageProvider] = None,
    ) -> AuthType:
        """
        Create authentication for the specified registered client
        application.

        Developers of applications must register clients with
        Planet, and will be issued a Client ID as part of that process.
        Developers should register a client for each distinct application so
        that end-users may discretely manage applications permitted to access
        Planet APIs on their behalf.

        This method does not perform a user login to initialize a session.
        If not initialized out of band using the CLI, sessions must be initialized
        with the user_login() before API calls may be made.

        Parameters:
            client_id: Client ID
            requested_scopes: List of requested OAuth2 scopes
            callback_url: Client callback URL
            profile_name: User friendly name to use when saving the configuration
                to storage per the `save_state_to_storage` flag.  The profile name
                will be normalized to a file system compatible identifier,
                regardless of storage provider.
            save_state_to_storage: Boolean controlling whether login sessions
                should be saved to storage. When the default storage provider is
                used, they will be stored in a way that is compatible with
                the `planet` CLI.
            storage_provider: A custom storage provider to save session state
                for the application.
        """
        plauth_config_dict = _OIDC_AUTH_CLIENT_CONFIG__USER_SKEL
        plauth_config_dict["client_type"] = "oidc_auth_code"
        plauth_config_dict["client_id"] = client_id
        if requested_scopes:
            plauth_config_dict["scopes"] = requested_scopes
        plauth_config_dict["redirect_uri"] = callback_url

        if not profile_name:
            profile_name = client_id
        normalized_profile_name = Auth._normalize_profile_name(profile_name)

        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context_from_custom_config(
            client_config=plauth_config_dict,
            initial_token_data={},
            save_token_file=save_state_to_storage,
            profile_name=normalized_profile_name,
            save_profile_config=save_state_to_storage,
            storage_provider=storage_provider,
        )

        return Auth._from_plauth(pl_authlib_context)

    # TODO: add support for confidential clients
    @staticmethod
    def from_oauth_user_device_code(
        client_id: str,
        requested_scopes: typing.Optional[List[str]] = None,
        save_state_to_storage: bool = True,
        profile_name: typing.Optional[str] = None,
        storage_provider: typing.Optional[ObjectStorageProvider] = None
    ) -> AuthType:
        """
        Create authentication for the specified registered client
        application.

        Developers of applications must register clients with
        Planet, and will be issued a Client ID as part of that process.
        Developers should register a client for each distinct application so
        that end-users may discretely manage applications permitted to access
        Planet APIs on their behalf.

        This method does not perform a user login to initialize a session.

        This method does not perform a user login to initialize a session.
        If not initialized out of band using the CLI, sessions must be initialized
        with the device login methods before API calls may be made.

        Parameters:
            client_id: Client ID
            requested_scopes: List of requested OAuth2 scopes
            profile_name: User friendly name to use when saving the configuration
                to storage per the `save_state_to_storage` flag.  The profile name
                will be normalized to file system compatible identifier, regardless
                of the storage provider being used.
            save_state_to_storage: Boolean controlling whether login sessions
                should be saved to storage. When the default storage provider is
                used, they will be stored in a way that is compatible with
                the `planet` CLI.
            storage_provider: A custom storage provider to save session state
                for the application.
        """
        plauth_config_dict = _OIDC_AUTH_CLIENT_CONFIG__USER_SKEL
        plauth_config_dict["client_type"] = "oidc_device_code"
        plauth_config_dict["client_id"] = client_id
        if requested_scopes:
            plauth_config_dict["scopes"] = requested_scopes

        if not profile_name:
            profile_name = client_id
        normalized_profile_name = Auth._normalize_profile_name(profile_name)

        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context_from_custom_config(
            client_config=plauth_config_dict,
            initial_token_data={},
            save_token_file=save_state_to_storage,
            profile_name=normalized_profile_name,
            save_profile_config=save_state_to_storage,
            storage_provider=storage_provider,
        )

        return Auth._from_plauth(pl_authlib_context)

    @staticmethod
    def from_oauth_m2m(
        client_id: str,
        client_secret: str,
        requested_scopes: typing.Optional[List[str]] = None,
        save_state_to_storage: bool = True,
        profile_name: typing.Optional[str] = None,
        storage_provider: typing.Optional[planet_auth.ObjectStorageProvider] = None,
    ) -> AuthType:
        """
        Create authentication from the specified OAuth2 service account
        client ID and secret.

        Parameters:
            client_id: Planet service account client ID.
            client_secret: Planet service account client secret.
            requested_scopes: List of requested OAuth2 scopes
            profile_name: User friendly name to use when saving the configuration
                to storage per the `save_state_to_storage` flag.  The profile name
                will be normalized to a file system compatible identifier regardless
                of the storage provider being used.
            save_state_to_storage: Boolean controlling whether login sessions
                should be saved to storage. When the default storage provider is
                used, they will be stored in a way that is compatible with
                the `planet` CLI.
            storage_provider: A custom storage provider to save session state
                for the application.
        """
        plauth_config_dict = _OIDC_AUTH_CLIENT_CONFIG__M2M_SKEL
        plauth_config_dict["client_id"] = client_id
        plauth_config_dict["client_secret"] = client_secret
        if requested_scopes:
            plauth_config_dict["scopes"] = requested_scopes

        if not profile_name:
            profile_name = client_id
        normalized_profile_name = Auth._normalize_profile_name(profile_name)

        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context_from_custom_config(
            client_config=plauth_config_dict,
            initial_token_data={},
            save_token_file=save_state_to_storage,
            profile_name=normalized_profile_name,
            save_profile_config=save_state_to_storage,
            storage_provider=storage_provider,
        )
        return Auth._from_plauth(pl_authlib_context)

    @staticmethod
    def _from_plauth(pl_authlib_context: planet_auth.Auth) -> AuthType:
        """
        Create authentication from the provided Planet Auth Library
        Authentication Context.  Generally, applications will want to use one
        of the Auth Library factory helpers to construct this context (See the
        factory class).

        This method is intended for advanced use cases where the developer
        has their own client ID registered, and is familiar with the
        Planet Auth Library.  (Registering client IDs is a feature of the
        Planet Platform not yet released to the public as of January 2025.)
        """
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_key(key: typing.Optional[str]) -> AuthType:
        """Obtain authentication from api key.

        Parameters:
            key: Planet API key
        """
        warnings.warn(
            "Planet API keys will be deprecated for most use cases."
            " Initialize an OAuth client, or create an OAuth service account."
            " Proceeding for now.",
            PendingDeprecationWarning)
        if not key:
            raise APIKeyAuthException('API key cannot be empty.')

        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_api_key_opt=key,
            save_token_file=False,
        )
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_file(
        filename: typing.Optional[typing.Union[str, pathlib.Path]] = None
    ) -> AuthType:
        """Create authentication from secret file.

        The default secret file is named `.planet.json` and is stored in the user
        directory. The file has a special format and should have been created
        with `Auth.write()`.

        Pending deprecation:
            OAuth2, which should replace API keys in most cases does not have
            a direct replacement for "from_file()" in many cases.
            The format of the `.planet.json file` is changing with the
            migration of Planet APIs to OAuth2.  With that, this method is
            also being deprecated as a means to bootstrap auth configuration
            with a simple API key.  For the time being this method will still
            be supported, but this method will fail if the file is present
            with only new configuration fields, and lacks the legacy API key
            field.

        Parameters:
            filename: Alternate path for the planet secret file.

        """
        warnings.warn("Auth.from_file() will be deprecated.",
                      PendingDeprecationWarning)
        plauth_config = {
            **_ProductionEnv.LEGACY_AUTH_AUTHORITY,
            "client_type": planet_auth.PlanetLegacyAuthClientConfig.meta().get(
                "client_type"),
        }
        pl_authlib_context = planet_auth.Auth.initialize_from_config_dict(
            client_config=plauth_config,
            token_file=filename or SECRET_FILE_PATH)
        # planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
        #    auth_profile_opt=_BuiltinConfigurationProvider.BUILTIN_PROFILE_NAME_LEGACY,
        #    token_file_opt=filename or SECRET_FILE_PATH
        # )
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_env(variable_name: typing.Optional[str] = None) -> AuthType:
        """Create authentication from environment variables.

        Reads the `PL_API_KEY` environment variable

        Pending Deprecation:
            This method is pending deprecation. The method `from_defaults()`
            considers environment variables and configuration files through
            the planet_auth and planet_auth_utils libraries, and works with
            legacy API keys, OAuth2 M2M clients, OAuth2 interactive profiles.
            This method should be used in most cases as a replacement.

        Parameters:
            variable_name: Alternate environment variable.
        """
        warnings.warn(
            "from_env() will be deprecated. Use from_defaults() in most"
            " cases, which will consider both environment variables and user"
            " configuration files.",
            PendingDeprecationWarning)
        variable_name = variable_name or planet_auth_utils.EnvironmentVariables.AUTH_API_KEY
        api_key = os.getenv(variable_name, None)
        return Auth.from_key(api_key)

    @staticmethod
    def from_login(email: str,
                   password: str,
                   base_url: typing.Optional[str] = None) -> AuthType:
        """Create authentication from login email and password.

        Note: To keep your password secure, the use of `getpass` is
        recommended.

        Parameters:
            email: Planet account email address.
            password: Planet account password.
            base_url: The base URL to use. Defaults to production
                authentication API base url.
        """
        warnings.warn(
            "Auth.from_login() has been deprecated.  Use Auth.from_user_session().",
            DeprecationWarning)
        raise DeprecationWarning(
            "Auth.from_login() has been deprecated.  Use Auth.from_user_session()."
        )

    @classmethod
    def from_dict(cls, data: dict) -> AuthType:
        raise DeprecationWarning("Auth.from_dict() has been deprecated.")

    def to_dict(self) -> dict:
        raise DeprecationWarning("Auth.to_dict() has been deprecated.")

    def store(self,
              filename: typing.Optional[typing.Union[str,
                                                     pathlib.Path]] = None):
        warnings.warn("Auth.store() has been deprecated.", DeprecationWarning)
        raise DeprecationWarning("Auth.store() has been deprecated.")

    @property
    def value(self):
        raise DeprecationWarning("Auth.value has been deprecated.")


class APIKeyAuthException(PlanetError):
    """exceptions thrown by APIKeyAuth"""
    pass


class _PLAuthLibAuth(AuthType):
    # The Planet Auth Library uses a "has a" authenticator pattern for its
    # planet_auth.Auth context class.  This SDK library employs a "is a"
    # authenticator design pattern for users of its Auth context obtained
    # from the constructors above. This class smooths over that design
    # difference as we move to using the Planet Auth Library.
    def __init__(self, plauth: planet_auth.Auth):
        self._plauth = plauth

    def auth_flow(self, r: httpx._models.Request):
        return self._plauth.request_authenticator().auth_flow(r)

    def user_login(
        self,
        allow_open_browser: typing.Optional[bool] = False,
        allow_tty_prompt: typing.Optional[bool] = False,
    ):
        self._plauth.login(
            allow_open_browser=allow_open_browser,
            allow_tty_prompt=allow_tty_prompt,
        )

    def device_user_login_initiate(self) -> dict:
        return self._plauth.device_login_initiate()

    def device_user_login_complete(self, login_initialization_info: dict):
        return self._plauth.device_login_complete(login_initialization_info)

    def is_initialized(self) -> bool:
        return self._plauth.request_authenticator_is_ready()
