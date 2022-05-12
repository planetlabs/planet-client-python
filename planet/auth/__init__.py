"""
The Planet Authentication package

This package contains functionality for authenticating to the service
and managing authentication material.  This package knows nothing about
the service itself apart from how to interact with authentication APIs.

This package understands multiple authentication mechanisms, whose details
are encapsulated in implementation subclasses that implement the primary
(abstract) base class interfaces.  These primary interfaces are as follows:

- AuthClient & AuthClientConfig - Responsible for interacting with
      authentication services to obtain a credential that may be used for
      other API requests. Different clients have different configuration
      needs, so a configuration type exists for each client type to keep
      configuration on rails.
- Credential - Models just a credential. Responsible for reading and
      writing saved credentials to disk and performing basic data
      validation.  Knows nothing about how to get a credential, or how to
      use a credential.
- RequestAuthenticator - Responsible for decorating API requests with a
      credential. Compatible with httpx and requests libraries.
- Auth - A container class for initializing and grouping a working set
      of the above.
"""

from .auth import Auth
from .auth_exception import AuthException
from .profile import Profile
from .auth_client import AuthClientConfig, AuthClient
from .credential import Credential
from .request_authenticator import RequestAuthenticator

from .oidc.auth_clients.auth_code_flow import \
    AuthCodePKCEClientConfig, \
    AuthCodePKCEAuthClient
from .oidc.auth_clients.client_credentials_flow import \
    ClientCredentialsClientSecretClientConfig, \
    ClientCredentialsClientSecretAuthClient, \
    ClientCredentialsPubKeyClientConfig, \
    ClientCredentialsPubKeyAuthClient
from .planet_legacy.auth_client import \
    PlanetLegacyAuthClientConfig, \
    PlanetLegacyAuthClient
from .static_api_key.auth_client import \
    StaticApiKeyAuthClientConfig, \
    StaticApiKeyAuthClient

from .oidc.oidc_credential import FileBackedOidcCredential
from .planet_legacy.legacy_api_key import FileBackedPlanetLegacyApiKey
from .static_api_key.static_api_key import FileBackedApiKey

from .oidc.request_authenticator import \
    RefreshingOidcTokenRequestAuthenticator, \
    RefreshOrReloginOidcTokenRequestAuthenticator
from .planet_legacy.request_authenticator import \
    PlanetLegacyRequestAuthenticator
from .static_api_key.request_authenticator import \
    FileBackedApiKeyRequestAuthenticator

__all__ = [
    Auth,
    AuthClient,
    AuthClientConfig,
    Credential,
    Profile,
    RequestAuthenticator,
    AuthException,
    AuthCodePKCEClientConfig,
    AuthCodePKCEAuthClient,
    ClientCredentialsClientSecretClientConfig,
    ClientCredentialsClientSecretAuthClient,
    ClientCredentialsPubKeyClientConfig,
    ClientCredentialsPubKeyAuthClient,
    FileBackedOidcCredential,
    RefreshingOidcTokenRequestAuthenticator,
    RefreshOrReloginOidcTokenRequestAuthenticator,
    PlanetLegacyAuthClientConfig,
    PlanetLegacyAuthClient,
    FileBackedPlanetLegacyApiKey,
    PlanetLegacyRequestAuthenticator,
    StaticApiKeyAuthClientConfig,
    StaticApiKeyAuthClient,
    FileBackedApiKey,
    FileBackedApiKeyRequestAuthenticator
]
