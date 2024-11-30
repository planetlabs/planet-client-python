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
import planet_auth_utils

from .constants import SECRET_FILE_PATH
from .auth_builtins import _ProductionEnv

AuthType = httpx.Auth


# planet_auth and planet_auth_utils code more or less entirely
# supersedes this class.  But, keeping this here for
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
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_api_key_opt=key,
            save_token_file=False,
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
        # There is no direct replacement for "from_file()", which expected the
        # file to only hold an API key (planet_auth_utils now can use it for
        # other things, too).  API keys will be deprecated for most use cases,
        # and user login will be different from service account login under
        # OAuth.  A user interactive OAuth client configuration that has been
        # initialized with a refresh token should function similarly, but is
        # different enough I do not think it should be shoehorned into this
        # method.
        warnings.warn("Auth.from_file() will be deprecated.", PendingDeprecationWarning)
        plauth_config = {
            **_ProductionEnv.LEGACY_AUTH_AUTHORITY,
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
        # TODO: we should consider how we want to expose initialization
        #       from the ENV for OAuth M2M
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
        # TODO: Need to provide instructions on what an application should do.
        #       It would not be hard to add username/password support to the
        #       PlanetAuthFactory and return Auth context initialized with
        #       the legacy protocol and API key, but we should encourage an
        #       OAuth login.
        #       At a code level, we should provide "from_oauth_m2m()" (Done)
        #       and something to use a user profile, which must be initialized
        #       interactively.  from_oauth_user(profile_name) seems reasonable,
        #       leaving the question of how to create and initialize non-built-in
        #       profiles. The plauth CLI and planet_auth library has code to
        #       do this, but I don't know if we should send users of the SDK
        #       to another SDK for the simple use cases.
        warnings.warn("Auth.from_login() has been deprecated.", DeprecationWarning)
        raise DeprecationWarning("Auth.from_login() has been deprecated.")

    @staticmethod
    def from_oauth_m2m(client_id: str, client_secret: str) -> AuthType:
        """Create authentication from OAuth service account client ID and secret.

        Parameters:
            client_id: Planet service account client ID.
            client_secret: Planet service account client secret.
        """
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_client_id_opt=client_id,
            auth_client_secret_opt=client_secret,
        )
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_plauth(pl_authlib_context: planet_auth.Auth):
        """
        Create authentication from the provided Planet Auth Library Authentication Context.
        Generally, applications will want to use one of the Auth Library helpers to
        construct this context (See the factory class).
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
