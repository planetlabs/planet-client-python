from planet.auth.oidc.api_clients.api_client import OIDCAPIClient

# class RevocationAPIException(OIDCAPIClientException):
#
#   def __init__(self, message=None, raw_response=None):
#        super().__init__(message, raw_response)


class RevocationAPIClient(OIDCAPIClient):

    def __init__(self, revocation_uri):
        super().__init__(revocation_uri)

    def _checked_revocation_call(self, params, request_auth):
        self._checked_post(params, request_auth)
        # if response.content:
        #    # No payload expected on success. All HTTP and known json error
        #    # checks in base class.
        #    raise RevocationAPIException(
        #        'Unexpected response from OIDC Revocation endpoint',
        #        response)

    def _revoke_token(self, token, token_hint, auth_enricher=None):
        params = {
            'token': token,
            'token_type_hint': token_hint,
            # 'client_id': client_id # FIXME? Requred? Part of enrichment?
        }
        request_auth = None
        if auth_enricher:
            params, request_auth = auth_enricher(params, self._endpoint_uri)
        self._checked_revocation_call(params, request_auth)

    def revoke_access_token(self, access_token, auth_enricher=None) -> None:
        self._revoke_token(access_token, 'access_token', auth_enricher)

    def revoke_refresh_token(self, refresh_token, auth_enricher=None) -> None:
        return self._revoke_token(refresh_token,
                                  'refresh_token',
                                  auth_enricher)
