from planet.auth.planet_legacy.legacy_api_key import FileBackedPlanetLegacyAPIKey
from planet.auth.request_authenticator import BearerTokenRequestAuthenticator


class PlanetLegacyRequestAuthenticator(BearerTokenRequestAuthenticator):
    def __init__(self, api_key_file: FileBackedPlanetLegacyAPIKey):
        super().__init__(token_body='', token_prefix='api-key')
        self._api_key_file = api_key_file

    def pre_request_hook(self):
        self._token_body = self._api_key_file.legacy_api_key()
