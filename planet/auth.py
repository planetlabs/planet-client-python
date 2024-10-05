# Copyright 2020 Planet Labs, Inc.
# Copyright 2022, 2024 Planet Labs PBC.
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

import planet_auth
import planet_auth_config
import planet_auth_utils

from .constants import SECRET_FILE_PATH


AuthType = httpx.Auth


# planet_auth and planet_auth_utils code more or less entirely
# entirely supersedes this class.  But, keeping this here for
# now for interface stability to bridge with the rest of the SDK.
class Auth(metaclass=abc.ABCMeta):
    """Handle authentication information for use with Planet APIs."""

    @staticmethod
    def from_key(key: str) -> AuthType:
        """Obtain authentication from api key.

        Parameters:
            key: Planet API key
        """
        warnings.warn("Planet API keys will be deprecated at some point."
                      " Initialize an OAuth client, or create an OAuth service account."
                      " Proceeding for now.", PendingDeprecationWarning)
        pl_authlib_context = planet_auth_utils.ProfileManager.initialize_auth_client_context(
            auth_profile_opt=planet_auth_utils.Profiles.BUILTIN_PROFILE_NAME_LEGACY,
            auth_api_key_opt=key,
            save_token_file=False
        )
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_file(
        filename: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> AuthType:
        """Create authentication from secret file.

        The secret file is named `.planet.json` and is stored in the user
        directory. The file has a special format and should have been created
        with `Auth.write()`.

        Parameters:
            filename: Alternate path for the planet secret file.

        """
        # There is no direct replacement for "from_file()", which held an API key.
        # API keys will be deprecated, and user login will be different from service account
        # login under OAuth.
        warnings.warn("Auth.from_file() will be deprecated.", PendingDeprecationWarning)
        plauth_config = {
            **planet_auth_config.Production.LEGACY_AUTH_AUTHORITY,
            "client_type": planet_auth.PlanetLegacyAuthClientConfig.meta().get("client_type"),
        }
        pl_authlib_context = planet_auth.Auth.initialize_from_config_dict(client_config=plauth_config,
                                                                token_file=filename or SECRET_FILE_PATH)
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_env(variable_name: typing.Optional[str] = None) -> AuthType:
        """Create authentication from environment variable.

        Reads the `PL_API_KEY` environment variable

        Parameters:
            variable_name: Alternate environment variable.
        """
        # There are just too many env vars and ways they interact and combine to continue to
        # support this method with the planet auth lib in the future.  Especially as we want
        # to move away from API keys and towards OAuth methods.
        warnings.warn("Auth.from_env() will be deprecated.", PendingDeprecationWarning)
        variable_name = variable_name or planet_auth.EnvironmentVariables.AUTH_API_KEY
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
        warnings.warn("Auth.from_login() and password based user login will be deprecated.", PendingDeprecationWarning)
        if base_url:
            warnings.warn("base_url is not longer a supported parameter to Auth.from_login()", DeprecationWarning)

        pl_authlib_context = planet_auth_utils.ProfileManager.initialize_auth_client_context(
            auth_profile_opt=planet_auth_utils.Profiles.BUILTIN_PROFILE_NAME_LEGACY
        )
        # Note: login() will save the resulting token
        pl_authlib_context.login(username=email, password=password, allow_tty_prompt=False)
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_plauth(pl_authlib_context: planet_auth.Auth):
        """
        Create authentication from the provided Planet Auth Library Authentication Context.
        Generally, applications will want to use one of the Auth Library helpers to
        construct this context, such as the `initialize_auth_client_context()` method.
        """
        return _PLAuthLibAuth(plauth=pl_authlib_context)


class _PLAuthLibAuth(Auth, AuthType):
    # The Planet Auth Library uses a "has a" authenticator pattern for its
    # planet_auth.Auth context class.  This SDK library employs a "is a"
    # authenticator design pattern for user's of its Auth context obtained
    # from the constructors above. This class smooths over that design
    # difference as we move to using the Planet Auth Library.
    def __init__(self, plauth: planet_auth.Auth):
        self._plauth = plauth

    def auth_flow(self, r: httpx._models.Request):
        return self._plauth.request_authenticator().auth_flow(r)
