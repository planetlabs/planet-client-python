from planet.auth.oidc.auth_clients.auth_code_flow import \
    AuthCodePKCEClientConfig
from planet.auth.planet_legacy.auth_client import \
    PlanetLegacyAuthClientConfig
from planet.constants import \
    DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT


DEFAULT_OIDC_AUTH_CLIENT_CONFIG = AuthCodePKCEClientConfig(
    # The well known OIDC client that is the Planet Python CLI.
    # Developers should register their own clients so that users may
    # manage grants for different applications.  Registering applications
    # also allows for application specific URLs or auth flow selection.
    # FIXME: a better URL for production
    auth_server='https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7',
    client_id='0oa2scq915nekGLum4x7',
    # FIXME: we need a public URL configured in the client ID in our Auth
    #      Provider for 'recirect_uri' that can catch the redirect for
    #      --no-open-browser use cases.
    redirect_uri='http://localhost:8080/login/callback_code',
    local_redirect_uri='http://localhost:8080',
    default_request_scopes=['planet', 'profile', 'openid', 'offline_access']
)

LEGACY_AUTH_CLIENT_CONFIG = PlanetLegacyAuthClientConfig(
    legacy_auth_endpoint=DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT)
