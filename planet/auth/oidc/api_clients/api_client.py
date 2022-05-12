import requests

from abc import ABC

from planet.auth.auth_client import AuthClientException


class OidcApiClient(ABC):
    """
    Base class that provides utility functions common to interactions with
    any of the OIDC endpoints.
    """

    def __init__(self, endpoint_uri):
        self._endpoint_uri = endpoint_uri

    def __check_http_error(self, response):
        if not response.ok:
            raise OidcApiClientException(
                message="HTTP error from OIDC endpoint at {}: {}: {}".format(
                    self._endpoint_uri, response.status_code, response.reason),
                raw_response=response)

    def __check_oidc_payload_json_error(self, response):
        if response.content:
            if not response.headers.get('content-type') == 'application/json':
                return

            json_response = response.json()

            # Irritatingly, I've seen multiple error payload schemas
            if json_response.get('error'):
                raise OidcApiClientException(
                    message='Error from OIDC endpoint at {}: {}: {}'.format(
                        self._endpoint_uri,
                        json_response.get('error'),
                        json_response.get('error_description')),
                    raw_response=response)

            if json_response.get('errorCode'):
                raise OidcApiClientException(
                    message='Error from OIDC endpoint at {}: {}: {}'.format(
                        self._endpoint_uri,
                        json_response.get('errorCode'),
                        json_response.get('errorSummary')),
                    raw_response=response)

    @staticmethod
    def __checked_json_response(response):
        json_response = None
        if response.content:
            if not response.headers.get('content-type') == 'application/json':
                raise OidcApiClientException(
                    message='Expected json content-type, but got {}'.format(
                        response.headers.get('content-type')),
                    raw_response=response)
            json_response = response.json()
        if not json_response:
            raise OidcApiClientException(
                'Response was not understood. Expected JSON response payload,'
                ' but none was found.',
                response)
        return json_response

    def __check_response(self, response):
        # Check for the json error first so we throw a more specific parsed
        # error if we understand it, regardless of HTTP status code.
        self.__check_oidc_payload_json_error(response)
        self.__check_http_error(response)

    def _checked_get(self, params, request_auth):
        response = requests.get(self._endpoint_uri,
                                params=params,
                                auth=request_auth)
        self.__check_response(response)
        return response

    def _checked_post(self, params, request_auth):
        response = requests.post(
            self._endpoint_uri,
            # Note: is the data/params crossing confusing? This was born out
            #       of some OIDC services accepting either in some cases,
            #       and others not doing so.
            data=params,
            auth=request_auth,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.__check_response(response)
        return response

    def _checked_post_json_response(self, params, request_auth):
        return self.__checked_json_response(
            self._checked_post(params, request_auth))

    def _checked_get_json_response(self, params, request_auth):
        return self.__checked_json_response(
            self._checked_get(params, request_auth))


class OidcApiClientException(AuthClientException):

    def __init__(self, message=None, raw_response=None):
        super().__init__(message)
        self.raw_response = raw_response
