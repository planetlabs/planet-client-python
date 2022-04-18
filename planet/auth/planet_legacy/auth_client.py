import getpass
import jwt
import requests

from planet.auth.auth_client import AuthClientConfig, AuthClient, AuthClientException
from planet.auth.planet_legacy.legacy_api_key import FileBackedPlanetLegacyAPIKey
from planet.constants import DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT


class PlanetLegacyAuthClientConfig(AuthClientConfig):
    def __init__(self,
                 legacy_auth_endpoint=DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT,
                 **kwargs):
        super().__init__(**kwargs)
        self.legacy_auth_endpoint = legacy_auth_endpoint


class PlanetLegacyAuthClientException(AuthClientException):
    def __init__(self, message=None, raw_response=None):
        super().__init__(message)
        self.raw_response = raw_response


class PlanetLagacyAuthClient(AuthClient):
    def __init__(self, legacy_client_config: PlanetLegacyAuthClientConfig):
        super().__init__(legacy_client_config)
        self._legacy_client_config = legacy_client_config

    @staticmethod
    def _prepare_auth_payload(username, password):
        data = {
            'email': username,
            'password': password
        }
        return data

    def _check_http_error(self, response):
        if not response.ok:
            raise PlanetLegacyAuthClientException(
                message="HTTP error from endpoint at {}: {}: {}".format(
                    self._legacy_client_config.legacy_auth_endpoint,
                    response.status_code, response.reason),
                raw_response=response)

    def _check_json_payload(self, response):
        json_response = None
        if response.content:
            if not response.headers.get('content-type') == 'application/json':
                raise PlanetLegacyAuthClientException(
                    message='Expected json content-type, but got {}'.format(response.headers.get('content-type')),
                    raw_response=response)
            json_response = response.json()
        if not json_response:
            raise PlanetLegacyAuthClientException(
                message='Response from authentication endpoint {} was not understood.'
                        ' Expected JSON response payload, but none was found.'
                        .format(self._legacy_client_config.legacy_auth_endpoint),
                raw_response=response)
        return json_response

    @staticmethod
    def _parse_json_response(response, json_response):
        token_jwt = json_response.get('token')
        if not token_jwt:
            raise PlanetLegacyAuthClientException(
                message='Authorization response did not include expected field "token"',
                raw_response=response)

        # XXX - The token is signed with a symmetric key.  The client does not
        # posses this key, and cannot verify the JWT.
        decoded_jwt = jwt.decode(token_jwt, options={'verify_signature': False})
        api_key = decoded_jwt.get('api_key')
        if not api_key:
            raise PlanetLegacyAuthClientException(
                message='Authorization response did not include expected field "api_key"'
                        ' in the returned token',
                raw_response=response)

        return api_key

    def _checked_auth_request(self, auth_data):
        response = requests.post(
            self._legacy_client_config.legacy_auth_endpoint,
            json=auth_data)
        self._check_http_error(response)
        json_response = self._check_json_payload(response)
        api_key = self._parse_json_response(response, json_response)
        return api_key

    def login(self, username=None, password=None, **kwargs):
        if not username:
            username = input('Email: ')
        if not password:
            password = getpass.getpass(prompt='Password: ')
        auth_payload = self._prepare_auth_payload(username, password)
        api_key = self._checked_auth_request(auth_payload)
        return FileBackedPlanetLegacyAPIKey(api_key=api_key)

