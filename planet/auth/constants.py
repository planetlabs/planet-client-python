'''
Constants used in the planet.auth packages
'''

ENV_API_KEY = 'PL_API_KEY'
ENV_AUTH_AUDIENCE = 'PL_AUTH_AUDIENCE'
ENV_AUTH_CLIENT_CONFIG_FILE = 'PL_AUTH_CLIENT_CONFIG_FILE'
ENV_AUTH_PASSWORD = 'PL_AUTH_PASSWORD'
ENV_AUTH_PROFILE = 'PL_AUTH_PROFILE'
ENV_AUTH_SCOPE = 'PL_AUTH_SCOPE'
ENV_AUTH_TOKEN_FILE = 'PL_AUTH_TOKEN_FILE'
ENV_AUTH_USERNAME = 'PL_AUTH_USERNAME'

AUTH_CONFIG_FILE_PLAIN = 'auth_client.json'
AUTH_CONFIG_FILE_SOPS = 'auth_client.sops.json'
TOKEN_FILE_PLAIN = 'token.json'
TOKEN_FILE_SOPS = 'token.sops.json'

# FIXME: we need a better URL for this public interface, that doesn't embed
#    implementation details like a specific ID.
PLANET_OAUTH_SERVER = 'https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7'
PLANET_LEGACY_AUTH_ENDPOINT = 'https://api.planet.com/v0/auth/login'

SDK_OIDC_AUTH_CLIENT_CONFIG_DICT = {
    # The well known OIDC client that is the Planet Python CLI.
    # Developers should register their own clients so that users may
    # manage grants for different applications.  Registering applications
    # also allows for application specific URLs or auth flow selection.
    "client_type": "oidc_auth_code",
    "auth_server": PLANET_OAUTH_SERVER,
    "client_id": "0oa2scq915nekGLum4x7",
    # FIXME: we need a public URL configured in the client ID in our Auth
    #      Provider for 'recirect_uri' that can catch the redirect for
    #      --no-open-browser use cases.
    "redirect_uri": "http://localhost:8080/login/callback",
    "local_redirect_uri": "http://localhost:8080",
    "default_request_scopes":
    ["planet", "offline_access", "openid", "profile"]
}

LEGACY_AUTH_CLIENT_CONFIG_DICT = {
    "client_type": "planet_legacy",
    "legacy_auth_endpoint": PLANET_LEGACY_AUTH_ENDPOINT
}

NOOP_AUTH_CLIENT_CONFIG_DICT = {
    "client_type": "none",
}

DEFAULT_AUTH_CLIENT_CONFIG_DICT = SDK_OIDC_AUTH_CLIENT_CONFIG_DICT
