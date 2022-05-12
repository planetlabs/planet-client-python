from planet.auth.planet_legacy.legacy_api_key import \
    FileBackedPlanetLegacyApiKey
from planet.auth.request_authenticator import \
    RequestAuthenticator


class PlanetLegacyRequestAuthenticator(RequestAuthenticator):

    def __init__(self, api_key_file: FileBackedPlanetLegacyApiKey):
        super().__init__(token_body='', token_prefix='api-key')
        self._api_key_file = api_key_file

    def pre_request_hook(self):
        self._token_body = self._api_key_file.legacy_api_key()
