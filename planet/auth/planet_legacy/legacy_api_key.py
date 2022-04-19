from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException


class FileBackedPlanetLegacyAPIKey(Credential):
    def __init__(self, api_key=None, api_key_file=None):
        super().__init__(data={'key': api_key}, file_path=api_key_file)

    def assert_valid(self):
        super().assert_valid()
        if not self._data.get('key'):
            raise FileBackedJsonObjectException("'key' not found in file " + str(self._file_path))

    def legacy_api_key(self):
        return self.lazy_load_get('key')
