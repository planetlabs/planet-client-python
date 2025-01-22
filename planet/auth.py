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
from typing import List

import planet_auth
import planet_auth_utils

from .constants import SECRET_FILE_PATH
from .auth_builtins import _ProductionEnv, _BuiltinConfigurationProvider, _OIDC_AUTH_CLIENT_CONFIG__SKEL
from .exceptions import PlanetError

AuthType = httpx.Auth


# planet_auth and planet_auth_utils code more or less entirely
# supersedes this class.  But, keeping this here for
# now for interface stability and to bridge with the rest of the SDK.
class Auth(metaclass=abc.ABCMeta):
    """Handle authentication information for use with Planet APIs."""

    @staticmethod
    def from_user_defaults() -> AuthType:
        """
        Create authentication from user defaults. Defaults take into
        account environment variables (highest priority), user configuration
        saved to `~/.planet.json` (next priority), and built-in defaults
        (lowest priority).

        Users may use the `planet auth login` command to initialize
        configuration files.

        Environment Variables:
            PL_AUTH_PROFILE: Specify a custom planet_auth library auth
                client profile (Advanced use cases)
            PL_AUTH_CLIENT_ID: Specify an OAuth2 M2M client ID
            PL_AUTH_CLIENT_SECRET: Specify an OAuth2 M2M client secret
            PL_AUTH_API_KEY: Specify a legacy Planet API key
        """
        return _PLAuthLibAuth(plauth=planet_auth_utils.PlanetAuthFactory.
                              initialize_auth_client_context())

    # TODO: It feels like we should accept an auth profile so a user
    #     can manage multiple identities.  But that's also far broader than
    #     "OAuth user interactive" session, since the auth implementation
    #     configured by a profile could be anything.
    #     It also feels like we need a method that accepts client IDs
    #     managed by the developer so they can initialize the library
    #     to use the specified client ID of the larger application built
    #     on top of the library (e.g. QGIS)
    @staticmethod
    def from_oauth_user_session():
        """
        Create authentication for a user whose initialized login information
        has been saved to `~/.planet.json` and `~/.planet/`.
        A user should perform a login to initialize this session out-of-band
        using the command `planet auth login`.

        To initialize this session programmatically, you must complete an
        OAuth2 user login flow.  This involves initiating a request to the
        authorization server, the user completing authentication using a
        web browser out of process, and finalizing the authentication and
        authorization in process and saving the session information that will
        be used to make API requests.

        Most properly, this process uses IDs that are specific to the
        application.  The exact process that should be used to complete
        login is specific to the particulars of the application.
        """
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_profile_opt=_BuiltinConfigurationProvider.
            BUILTIN_PROFILE_NAME_PLANET_USER)
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    # TODO:
    #  I think we need something like this for developers of user interactive
    #  applications (e.g. QGIS), but as of January 2025 we do not have a way
    #  for developers to register user interactive client on the platform,
    #  or a way for users of such applications to revoke such authorizations.
    #  Even without this, we may white glove client IDs for partners before
    #  it is a generally available feature.
    # TODO:
    #  This works to initialize the library auth client, but DOES NOT
    #  establish a user session.  If on disk storage can be used, that
    #  can be done out of band via the CLI.  If in memory operations
    #  are desired, that will not work.
    #  In either case, what needs to happen is that
    #  planet.auth._PLAuthLibAuth._plauth.login() needs to be invoked.
    #  If disk storage is used, that only needs to happen once and the results
    #  will be picked up from disk by this Auth init method. If not,
    #  that needs to happen for every process invocation, since tokens
    #  will not be saved, and refresh cannot be performed.
    #  User experience is greatly served by being able to save to disk.
    @staticmethod
    def beta_from_oauth_client_config(
            client_id: str,
            requested_scopes: List[str],
            save_token_file: bool = True) -> AuthType:
        """
        Beta.  Feature not yet supported for public use.
        """
        plauth_config_dict = _OIDC_AUTH_CLIENT_CONFIG__SKEL
        plauth_config_dict["client_id"] = client_id
        plauth_config_dict["scopes"] = requested_scopes
        #  TBD: How flexible will we be in terms of supported flows OAuth flows?
        plauth_config_dict["client_type"] = "oidc_device_code"

        # Other client types have other needs.
        # Confidential clients need client secrets.
        # Auth code clients need callback URLs.
        # plauth_config_dict["client_secret"] = client_id # Only needed if we support certain types of clients

        # TODO
        #    This will not write the constructed config to the user's
        #    ~/.planet/ dir the way a conf constructed by a cli command like
        #    `planet auth login --client-id XXX --client-secret YYY` will.
        #    The intent of doing it through the planet_auth_utils factory is so we
        #    play well with tooling like the CLI.  This maybe does not quite achieve
        #    the desired result.  We are saving tokens in the right place, but not
        #    giving the CLI all it needs to co-manage said tokens with whatever app
        #    is being build on the library.  Those are perhaps separate decisions,
        #    anyway.
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context_with_config(
            client_config=plauth_config_dict,
            # TODO - Probably need a user friendly profile name
            #  We should also probably agree with what's registered in the Auth server.
            profile_name=client_id.lower(),
            save_token_file=save_token_file)
        return Auth.from_plauth(pl_authlib_context)

    @staticmethod
    def from_oauth_m2m(client_id: str, client_secret: str) -> AuthType:
        """Create authentication from the specified OAuth2 service account
         client ID and secret.

        Parameters:
            client_id: Planet service account client ID.
            client_secret: Planet service account client secret.
        """
        pl_authlib_context = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
            auth_client_id_opt=client_id,
            auth_client_secret_opt=client_secret,
            # auth_profile_opt=_BuiltinConfigurationProvider.BUILTIN_PROFILE_NAME_PLANET_M2M,
        )
        return _PLAuthLibAuth(plauth=pl_authlib_context)

    @staticmethod
    def from_plauth(pl_authlib_context: planet_auth.Auth) -> AuthType:
        """
        Create authentication from the provided Planet Auth Library
        Authentication Context.  Generally, applications will want to use one
        of the Auth Library factory helpers to construct this context (See the
        factory class).

        This method is intended for advanced use cases where the developer
        as their own client ID registered.  (A feature of the Planet Platform
        not yet released to the public as of January 2025.)
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
            "client_type":
            planet_auth.PlanetLegacyAuthClientConfig.meta().get("client_type"),
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
            " cases, which will consider environment variables.",
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


class _PLAuthLibAuth(Auth, AuthType):
    # The Planet Auth Library uses a "has a" authenticator pattern for its
    # planet_auth.Auth context class.  This SDK library employs a "is a"
    # authenticator design pattern for user's of its Auth context obtained
    # from the constructors above. This class partially smooths over that
    # design difference as we move to using the Planet Auth Library.
    def __init__(self, plauth: planet_auth.Auth):
        self._plauth = plauth

    def auth_flow(self, r: httpx._models.Request):
        return self._plauth.request_authenticator().auth_flow(r)
