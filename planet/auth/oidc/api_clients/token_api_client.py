from planet.auth.oidc.api_clients.api_client import \
    OidcApiClient, OidcApiClientException


class TokenApiException(OidcApiClientException):

    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class TokenApiClient(OidcApiClient):

    def __init__(self, token_uri):
        super().__init__(token_uri)

    @staticmethod
    def _check_token_response(json_response):
        if not json_response.get('expires_in'):
            raise TokenApiException(
                message='Invalid token received. Missing expires_in field.')

    def _checked_call(self, token_params, auth_enricher=None):
        request_auth = None
        if auth_enricher:
            token_params, request_auth = auth_enricher(token_params,
                                                       self._endpoint_uri)

        json_response = self._checked_post_json_response(
            token_params, request_auth)
        self._check_token_response(json_response)
        return json_response

    def get_token_from_refresh(self,
                               client_id,
                               refresh_token,
                               requested_scopes=None):
        data = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'refresh_token': refresh_token
        }
        if requested_scopes:
            # You can request down-scope on refresh, but the refresh token
            # remains potent.
            data['scope'] = ' '.join(requested_scopes)
        # FIXME: can you change audience on refresh?

        return self._checked_call(data)

    def get_token_from_client_credentials(self,
                                          client_id,
                                          requested_scopes=None,
                                          requested_audiences=None,
                                          auth_enricher=None):
        data = {
            'grant_type': 'client_credentials',
            # Client id, secret, or assertion come from enricher.
            # 'client_id': client_id,
            # 'client_secret': client_secret
            # 'client_assertion_type':
            #        'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            #  client_assertion': signed_jwt
        }
        if requested_scopes:
            data['scope'] = ' '.join(requested_scopes)
        if requested_audiences:
            data['audience'] = ' '.join(requested_audiences)

        return self._checked_call(data, auth_enricher)

    def get_token_from_code(self,
                            redirect_uri,
                            client_id,
                            code,
                            code_verifier,
                            auth_enricher=None):
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code,
            'code_verifier': code_verifier,
            # 'client_id': client_id,  # The job of the enricher.
            # 'request_auth': None     # Where did this come from?
        }

        return self._checked_call(data, auth_enricher)
