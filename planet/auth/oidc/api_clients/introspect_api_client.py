from planet.auth.oidc.api_clients.api_client import OIDCAPIClient, OIDCAPIClientException


class IntrospectionAPIException(OIDCAPIClientException):
    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class IntrospectionAPIClient(OIDCAPIClient):
    def __init__(self, introspect_uri=None):
        super().__init__(introspect_uri)

    def _checked_introspection_call(self, validate_params, auth):
        json_response = self._checked_post_json_response(validate_params, auth)
        if not bool(json_response.get('active')):
            raise IntrospectionAPIException('Token is not active')
        return json_response

    def _validate_token(self, token, token_hint, auth_enricher):
        params = {
            'token': token,
            'token_type_hint': token_hint,
            # 'client_id': client_id # FIXME: Required?? Or part of enrichment?
        }
        request_auth = None
        if auth_enricher:
            params, request_auth = auth_enricher(params, self._endpoint_uri)
        return self._checked_introspection_call(params, request_auth)

    # TODO: it might be nice to have "introspect_*_token() calls that don't throw on invalid tokens, but only throw
    #       when there is an error making the call.

    def validate_access_token(self, access_token, auth_enricher=None):  # FIXME: strict typing for the enricher
        return self._validate_token(access_token, 'access_token', auth_enricher)

    def validate_id_token(self, id_token, auth_enricher=None):
        return self._validate_token(id_token, 'id_token', auth_enricher)

    def validate_refresh_token(self, refresh_token, auth_enricher):
        return self._validate_token(refresh_token, 'refresh_token', auth_enricher)
