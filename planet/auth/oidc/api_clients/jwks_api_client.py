from planet.auth.oidc.api_clients.api_client import \
    OIDCAPIClient,\
    OIDCAPIClientException


class JwksAPIException(OIDCAPIClientException):
    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class JwksAPIClient(OIDCAPIClient):
    def __init__(self, jwks_uri):
        super().__init__(jwks_uri)

    def _checked_fetch(self):
        return self._checked_get_json_response(None, None)

    def jwks(self):
        return self._checked_fetch()

    def jwks_keys(self):
        jwks_response = self.jwks()
        jwks_keys = jwks_response.get('keys')
        if not jwks_keys:
            raise JwksAPIException(message='JWKS endpoint response did not include "keys" data')
        return jwks_keys
