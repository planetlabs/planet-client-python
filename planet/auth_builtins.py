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
os.environ["PL_BUILTIN_AUTH_CONFIG_PROVIDER"] = "planet.auth_builtins._BuiltinConfigurationProvider"

class _ProductionEnv:
    PRIMARY_PUBLIC_OAUTH_AUTHORITY_AUTH0 = {
        "_comment": "OIDC/OAuth server used by Planet Public API endpoints",
        "auth_server": "https://login.planet.com/",
        "audiences": ["https://api.planet.com/"]
    }
    PRIMARY_PUBLIC_OAUTH_AUTHORITY_SENTINELHUB = {
        "_comment": "OIDC/OAuth server used by Planet Public API endpoints",
        "auth_server": "https://services.sentinel-hub.com/auth/realms/main",
        "audiences": ["https://api.planet.com/"]
    }
    LEGACY_AUTH_AUTHORITY = {
        "_comment": "Planet legacy JWT auth server used by Planet Public API endpoints",
        "legacy_auth_endpoint": "https://api.planet.com/v0/auth/login"
    }
    PRIMARY_PUBLIC_OAUTH_AUTHORITIES = [
        PRIMARY_PUBLIC_OAUTH_AUTHORITY_AUTH0,
        PRIMARY_PUBLIC_OAUTH_AUTHORITY_SENTINELHUB,
    ]

_OIDC_AUTH_CLIENT_CONFIG__SDK_PROD = {
    # The well known OIDC client that is the Planet Python CLI.
    # Developers should register their own clients so that users may
    # manage grants for different applications.  Registering applications
    # also allows for application specific URLs or auth flow selection.
    **_ProductionEnv.PRIMARY_PUBLIC_OAUTH_AUTHORITY_AUTH0,
    "client_type": "oidc_device_code",
    "client_id": "49lHVBYlXCdfIYqE1B9zeXt0iFHSXees",
    "scopes": ["planet", "offline_access", "openid", "profile", "email"],
}

_OIDC_AUTH_CLIENT_CONFIG__M2M_PROD = {
    **_ProductionEnv.PRIMARY_PUBLIC_OAUTH_AUTHORITY_SENTINELHUB,
    "client_type": "oidc_client_credentials_secret",
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

    # fmt: off
    ##
    ## OAuth production environment profiles
    ##
    # Real
    BUILTIN_PROFILE_NAME_PLANET_USER          = "planet-user"
    BUILTIN_PROFILE_NAME_PLANET_M2M           = "planet-m2m"
    # Aliases
    # BUILTIN_PROFILE_NAME_PROD                 = "prod"
    # BUILTIN_PROFILE_NAME_PROD_M2M             = "prod-m2m"
    # BUILTIN_PROFILE_NAME_PROD_AUTH0           = "prod-auth0"
    # BUILTIN_PROFILE_NAME_PROD_SENTINEL_HUB    = "prod-sentinel-hub"

    ##
    ## Profiles that use Planet's old (pre-OAuth) based auth protocol
    ##
    BUILTIN_PROFILE_NAME_LEGACY         = "legacy"

    ##
    ## Misc auth profiles
    ##
    BUILTIN_PROFILE_NAME_NONE    = "none"
    BUILTIN_PROFILE_NAME_DEFAULT = "default"

    ##
    ## Default that should be used when no other selection has been made
    ##
    DEFAULT_PROFILE = BUILTIN_PROFILE_NAME_PLANET_USER

    _builtin_profile_auth_client_configs = {
        ## OAuth Client Configs
        BUILTIN_PROFILE_NAME_PLANET_USER          : _OIDC_AUTH_CLIENT_CONFIG__SDK_PROD,
        BUILTIN_PROFILE_NAME_PLANET_M2M           : _OIDC_AUTH_CLIENT_CONFIG__M2M_PROD,

        # Planet Legacy Protocols
        BUILTIN_PROFILE_NAME_LEGACY            : _LEGACY_AUTH_CLIENT_CONFIG__PROD,

        # Misc
        BUILTIN_PROFILE_NAME_NONE              : _NOOP_AUTH_CLIENT_CONFIG,
    }

    _builtin_profile_aliases = {
        BUILTIN_PROFILE_NAME_DEFAULT              : DEFAULT_PROFILE,
        # BUILTIN_PROFILE_NAME_PROD                 : BUILTIN_PROFILE_NAME_PLANET_USER,
        # BUILTIN_PROFILE_NAME_PROD_M2M             : BUILTIN_PROFILE_NAME_PLANET_M2M,
        # BUILTIN_PROFILE_NAME_PROD_AUTH0           : BUILTIN_PROFILE_NAME_PLANET_USER,
        # BUILTIN_PROFILE_NAME_PROD_SENTINEL_HUB    : BUILTIN_PROFILE_NAME_PLANET_M2M,
    }
    _builtin_profile_default_by_client_type = {
        "oidc_device_code"               : BUILTIN_PROFILE_NAME_PLANET_USER,
        "oidc_auth_code"                 : BUILTIN_PROFILE_NAME_PLANET_USER,
        "oidc_client_credentials_secret" : BUILTIN_PROFILE_NAME_PLANET_M2M,
        "planet_legacy"                  : BUILTIN_PROFILE_NAME_LEGACY,
    }
    _builtin_trust_realms: Dict[str, Optional[List[dict]]] = {
        "PRODUCTION": _ProductionEnv.PRIMARY_PUBLIC_OAUTH_AUTHORITIES,
        "CUSTOM": None,
    }
    # fmt: on

    def builtin_client_authclient_config_dicts(self) -> Dict[str, dict]:
        return self._builtin_profile_auth_client_configs

    def builtin_client_profile_aliases(self) -> Dict[str, str]:
        return self._builtin_profile_aliases

    def builtin_default_profile_by_client_type(self) -> Dict[str, str]:
        pass

    def builtin_default_profile(self) -> str:
        return self.BUILTIN_PROFILE_NAME_DEFAULT

    def builtin_trust_environment_names(self) -> List[str]:
        return list(_BuiltinConfigurationProvider._builtin_trust_realms.keys())

    def builtin_trust_environments(self) -> Dict[str, Optional[List[dict]]]:
        return _BuiltinConfigurationProvider._builtin_trust_realms
