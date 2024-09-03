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
import pathlib
import typing
import warnings
import httpx

import planet_auth
import planet_auth_config

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
        # TODO : document preferred new method in the warning.  User OAuth flows should be favored
        #        for user API access. M2M OAuth flows for other use cases.
        warnings.warn("Auth.from_key() will be deprecated.", PendingDeprecationWarning)
        plauth_config = {
            "client_type": planet_auth.PlanetLegacyAuthClientConfig.meta().get("client_type"),
            "api_key": key,
        }
        pl_authlib_context = planet_auth.Auth.initialize_from_config_dict(client_config=plauth_config)
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
        # TODO - Document preferred replacement.  A token file from PLAuth's Legacy client
        #        is formatted to be compatible with this library's .planet.json format files.
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
        # TODO: document all the new ways the env can set things up for OAuth clients.
        if variable_name:
            warnings.warn("The variable_name parameter has been deprecated from planet.Auth.from_env().", DeprecationWarning)
        pl_authlib_context = planet_auth.Auth.initialize_from_env()
        return _PLAuthLibAuth(plauth=pl_authlib_context)

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
        # TODO - PLAuth.login will save the credential if the file is set.  Handle this case?
        #        We need to conditionally set the token file in the initialize call.
        # TODO - update warning with directions on what to replace this with. (maybe from_user_oauth_login?)
        warnings.warn("Auth.from_login will be deprecated.", PendingDeprecationWarning)
        plauth_config = {
            **planet_auth_config.Production.LEGACY_AUTH_AUTHORITY,
            "client_type": planet_auth.PlanetLegacyAuthClientConfig.meta().get("client_type"),
        }
        if base_url:
            plauth_config["legacy_auth_endpoint"] = base_url

        pl_authlib_context = planet_auth.Auth.initialize_from_config_dict(client_config=plauth_config)
        pl_authlib_context.login(username=email, password=password, allow_tty_prompt=False)
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_plauth(pl_authlib_context: planet_auth.Auth):
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
