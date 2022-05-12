from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException


class FileBackedPlanetLegacyApiKey(Credential):

    def __init__(self, api_key=None, api_key_file=None):
        if api_key:
            init_data = {'key': api_key}
        else:
            init_data = None
        super().__init__(data=init_data, file_path=api_key_file)

    def check_data(self, data):
        super().check_data(data)
        if not data.get('key'):
            raise FileBackedJsonObjectException("'key' not found in file " +
                                                str(self._file_path))

    def legacy_api_key(self):
        return self.lazy_get('key')
