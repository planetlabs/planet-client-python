# Copyright 2024 Planet Labs PBC.
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
import os
from typing import Dict, List, Optional
from planet_auth_utils.builtins_provider import BuiltinConfigurationProviderInterface

# Needs to be set at runtime (not necessarily at import time) for dependency injection to planet_auth_util
os.environ[
    "PL_AUTH_BUILTIN_CONFIG_PROVIDER"] = "planet.auth_builtins._BuiltinConfigurationProvider"


# No StrEnum in our lowest supported Python version
# class PlanetOAuthScopes(enum.StrEnum):
class PlanetOAuthScopes:
    """
    Planet OAuth2 Scopes
    """
    PLANET = "planet"
    OFFLINE_ACCESS = "offline_access"
    OPENID = "openid"
    PROFILE = "profile"
    EMAIL = "email"


class _ProductionEnv:
    OAUTH_AUTHORITY_USER = {
        "_comment": "OIDC/OAuth server used by Planet Public API endpoints",
        "auth_server": "https://login.planet.com/",
        "audiences": ["https://api.planet.com/"]
    }
    OAUTH_AUTHORITY_M2M = {
        "_comment": "OIDC/OAuth server used by Planet Public API endpoints",
        "auth_server": "https://services.sentinel-hub.com/auth/realms/main",
        "audiences": ["https://api.planet.com/"]
    }
    LEGACY_AUTH_AUTHORITY = {
        "_comment":
        "Planet legacy JWT auth server used by Planet Public API endpoints",
        "legacy_auth_endpoint": "https://api.planet.com/v0/auth/login"
    }
    PUBLIC_OAUTH_AUTHORITIES = [
        OAUTH_AUTHORITY_USER,
        OAUTH_AUTHORITY_M2M,
    ]


_SDK_CLIENT_ID_PROD = "49lHVBYlXCdfIYqE1B9zeXt0iFHSXees"

_OIDC_AUTH_CLIENT_CONFIG__SKEL = {
    **_ProductionEnv.OAUTH_AUTHORITY_USER,
    "scopes": [
        PlanetOAuthScopes.PLANET,
        PlanetOAuthScopes.OFFLINE_ACCESS,
        # PlanetOAuthScopes.OPENID,
        # PlanetOAuthScopes.PROFILE,
        # PlanetOAuthScopes.EMAIL
    ],
    # "client_type": "oidc_device_code",  # Must be provided when hydrating the SKEL
    # "client_id": _SDK_CLIENT_ID_PROD,   # Must be provided when hydrating the SKEL
}

_OIDC_AUTH_CLIENT_CONFIG__SDK_PROD = {
    # The well known OIDC client that is the Planet Python CLI.
    # Developers should register their own clients so that users may
    # manage grants for different applications.  Registering applications
    # also allows for application specific URLs or auth flow selection.
    **_OIDC_AUTH_CLIENT_CONFIG__SKEL,
    "client_type": "oidc_device_code",
    "client_id": _SDK_CLIENT_ID_PROD,
    # FIXME: scopes currently from SKEL.
    #  It would be better to have per-client defaults and limits enforced by the auth server
}

_OIDC_AUTH_CLIENT_CONFIG__M2M_PROD = {
    **_ProductionEnv.OAUTH_AUTHORITY_M2M,
    "client_type": "oidc_client_credentials_secret",
    # FIXME: we do not have scope or behavior parity between our M2M and our user OAuth authorities.
    "scopes": [],
    # "client_id": "__MUST_BE_USER_SUPPLIED__",
    # "client_secret": "__MUST_BE_USER_SUPPLIED__",
    # "scopes": ["planet"],
    # "audiences": [""]
}

_LEGACY_AUTH_CLIENT_CONFIG__PROD = {
    **_ProductionEnv.LEGACY_AUTH_AUTHORITY,
    "client_type": "planet_legacy",
}

_NOOP_AUTH_CLIENT_CONFIG = {
    "client_type": "none",
}


class _BuiltinConfigurationProvider(BuiltinConfigurationProviderInterface):
    """
    Concrete implementation of built-in client profiles for the planet_auth
    library that pertain to the Planet Lab's cloud service.
    """

    # Real
    #   Using the client ID as a profile name might be nice, but is tricky...
    #   We normalize directory paths to lower case. The auth implementation uses
    #   mixed case ID strings.  The odds of case normalized IDs colliding is low,
    #   but there is a bit of an off smell.
    # BUILTIN_PROFILE_NAME_SDKCLI_CLIENT_ID = _SDK_CLIENT_ID_PROD
    BUILTIN_PROFILE_NAME_PLANET_USER = "planet-user"
    BUILTIN_PROFILE_NAME_PLANET_M2M = "planet-m2m"
    BUILTIN_PROFILE_NAME_LEGACY = "legacy"
    BUILTIN_PROFILE_NAME_NONE = "none"

    # Aliases
    # BUILTIN_PROFILE_ALIAS_PLANET_USER = "planet-user"

    _builtin_profile_auth_client_configs: Dict[str, dict] = {
        # BUILTIN_PROFILE_NAME_SDKCLI_CLIENT_ID: _OIDC_AUTH_CLIENT_CONFIG__SDK_PROD,
        BUILTIN_PROFILE_NAME_PLANET_USER: _OIDC_AUTH_CLIENT_CONFIG__SDK_PROD,
        BUILTIN_PROFILE_NAME_PLANET_M2M: _OIDC_AUTH_CLIENT_CONFIG__M2M_PROD,
        BUILTIN_PROFILE_NAME_LEGACY: _LEGACY_AUTH_CLIENT_CONFIG__PROD,
        BUILTIN_PROFILE_NAME_NONE: _NOOP_AUTH_CLIENT_CONFIG,
    }

    _builtin_profile_aliases: dict[str, str] = {
        # BUILTIN_PROFILE_ALIAS_PLANET_USER: BUILTIN_PROFILE_NAME_SDKCLI_CLIENT_ID,
    }

    _builtin_profile_default_by_client_type = {
        "oidc_device_code": BUILTIN_PROFILE_NAME_PLANET_USER,
        "oidc_auth_code": BUILTIN_PROFILE_NAME_PLANET_USER,
        "oidc_client_credentials_secret": BUILTIN_PROFILE_NAME_PLANET_M2M,
        "planet_legacy": BUILTIN_PROFILE_NAME_LEGACY,
        "none": BUILTIN_PROFILE_NAME_NONE,
    }

    _builtin_trust_realms: Dict[str, Optional[List[dict]]] = {
        "PRODUCTION": _ProductionEnv.PUBLIC_OAUTH_AUTHORITIES,
        "CUSTOM": None,
    }

    def builtin_client_authclient_config_dicts(self) -> Dict[str, dict]:
        return self._builtin_profile_auth_client_configs

    def builtin_client_profile_aliases(self) -> Dict[str, str]:
        return self._builtin_profile_aliases

    def builtin_default_profile_by_client_type(self) -> Dict[str, str]:
        return self._builtin_profile_default_by_client_type

    def builtin_default_profile(self) -> str:
        # return self.BUILTIN_PROFILE_NAME_DEFAULT
        return self.BUILTIN_PROFILE_NAME_PLANET_USER

    def builtin_trust_environment_names(self) -> List[str]:
        return list(_BuiltinConfigurationProvider._builtin_trust_realms.keys())

    def builtin_trust_environments(self) -> Dict[str, Optional[List[dict]]]:
        return _BuiltinConfigurationProvider._builtin_trust_realms
