from planet.auth.oidc.auth_clients.auth_code_flow import AuthCodePKCEClientConfig


ENV_AUTH_CLIENT_CONFIG_FILE = 'PL_AUTH_CLIENT_CONFIG_FILE'
ENV_AUTH_PASSWORD='PL_AUTH_PASSWORD'
ENV_AUTH_PROFILE = 'PL_AUTH_PROFILE'
ENV_AUTH_SCOPES = 'PL_AUTH_SCOPES'
ENV_AUTH_TOKEN_FILE = 'PL_AUTH_TOKEN_FILE'
ENV_AUTH_USERNAME='PL_AUTH_USERNAME'
ENV_FOO_ID = 'PL_FOO_ID'
ENV_FOO_SERVICE_URL = 'PL_FOO_SERVICE_URL'
ENV_LOGLEVEL = 'PL_LOGLEVEL'

DEFAULT_OIDC_CLIENT_CONFIG = AuthCodePKCEClientConfig(
    # The well known OIDC client that is the Planet Python CLI.
    # Developers should register their own clients so that users may
    # manage grants for different applications.  Registering applications
    # also allows for application specific URLs or auth flow selection.
    # FIXME: a better URL for production
    auth_server='https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7',
    client_id='0oa2scq915nekGLum4x7',
    redirect_uri='http://localhost:8080',
    default_request_scopes=['planet', 'profile', 'openid', 'offline_access']
)

DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT = 'https://api.planet.com/v0/auth/login'
