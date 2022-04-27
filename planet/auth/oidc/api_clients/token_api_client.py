import jwt
import time
import uuid

from planet.auth.oidc.api_clients.api_client import \
    OIDCAPIClient, OIDCAPIClientException


class TokenAPIException(OIDCAPIClientException):

    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class TokenAPIClient(OIDCAPIClient):

    def __init__(self, token_uri):
        super().__init__(token_uri)

    @staticmethod
    def _check_token_response(json_response):
        if not json_response.get('expires_in'):
            raise TokenAPIException(
                message='Invalid token received. Missing expires_in field.')

    def _checked_call(self, token_params, request_auth=None):
        json_response = self._checked_post_json_response(
            token_params, request_auth)
        self._check_token_response(json_response)
        return json_response

    def _prepare_private_key_jwt(self, client_id, private_key):
        now = int(time.time())
        unsigned_jwt = {
            'iss': client_id,
            'sub': client_id,
            'aud': self._endpoint_uri,
            'iat': now,
            'exp': now + 300,
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(unsigned_jwt, private_key, algorithm="RS256")

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
        return self._checked_call(data)

    # FIXME: delete? When should we defer auth to the flow enricher vs had a
    #        bespoke methods. Enrichment for auth itself is slightly
    #        different than it is for any call that requires auth.
    def get_token_from_client_credentials_enrichment(self,
                                                     client_id,
                                                     requested_scopes=None,
                                                     auth_enricher=None):
        # FIXME: should client id come from enricher? It's a pretty intrinsic
        #        part of the client credential request.
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
        }
        if requested_scopes:
            data['scope'] = ' '.join(requested_scopes)

        if auth_enricher:
            data, auth = auth_enricher(data, self._endpoint_uri)

        return self._checked_call(data)

    def get_token_from_client_credentials_secret(self,
                                                 client_id,
                                                 client_secret,
                                                 requested_scopes=None):
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        if requested_scopes:
            data['scope'] = ' '.join(requested_scopes)

        # FIXME: should this be passed to checked_call() as the request auth?
        #     (See notes below. Don't recall all permutations)
        # request_auth = HTTPBasicAuth(client_id, client_secret)
        return self._checked_call(data)

    def get_token_from_client_credentials_pubkey(self,
                                                 client_id,
                                                 private_key,
                                                 requested_scopes=None):
        signed_jwt = self._prepare_private_key_jwt(client_id, private_key)
        data = {
            'grant_type': 'client_credentials',
            # client_id causes a "Cannot supply multiple client credentials."
            # error from Okta. Redundant with the signed assertion
            # 'client_id': client_id,
            'client_assertion_type':
            'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': signed_jwt
        }
        if requested_scopes:
            data['scope'] = ' '.join(requested_scopes)

        return self._checked_call(data)

    def get_token_from_code(self, redirect_uri, client_id, code,
                            code_verifier):
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code,
            'code_verifier': code_verifier,
            'client_id': client_id,
            'request_auth': None
        }

        return self._checked_call(data)
