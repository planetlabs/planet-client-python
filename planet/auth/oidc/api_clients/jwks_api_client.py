from planet.auth.oidc.api_clients.api_client import OIDCAPIClient, OIDCAPIClientException


class JwksAPIException(OIDCAPIClientException):
    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class JwksAPIClient(OIDCAPIClient):
    def __init__(self, jwks_uri):
        super().__init__(jwks_uri)
        raise JwksAPIException('API client not implemented for JWKS (TODO: compare to standard JWKS API client)')

    def _checked_jwks_call(self, params, request_auth):
        self._checked_post(params, request_auth)
