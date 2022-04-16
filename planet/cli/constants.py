from planet.auth.oidc.auth_clients.auth_code_flow import AuthCodePKCEClientConfig


DEFAULT_OIDC_CLIENT_CONFIG = AuthCodePKCEClientConfig(
    # The well known OIDC client that is the Planet Python CLI
    # FIXME: a better URL for production
    auth_server='https://account.planet.com/oauth2/aus2enhwueFYRb50S4x7',
    client_id='0oa2scq915nekGLum4x7',
    redirect_uri='http://localhost:8080',
    default_request_scopes=['planet', 'profile', 'openid', 'offline_access']
)
