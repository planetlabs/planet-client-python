from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException


class FileBackedAPIKey(Credential):
    def __init__(self, api_key=None, prefix=None, api_key_file=None):
        super().__init__(data={'api_key': api_key,
                               'bearer_token_prefix': prefix},
                         file_path=api_key_file)

    def assert_valid(self):
        super().assert_valid()
        if not self._data.get('api_key'):
            raise FileBackedJsonObjectException("'api_key' not found in file " + str(self._file_path))
        if not self._data.get('bearer_token_prefix'):
            raise FileBackedJsonObjectException("'bearer_token_prefix' not found in file " + str(self._file_path))

    def api_key(self):
        return self.lazy_load_get('api_key')

    def bearer_token_prefix(self):
        return self.lazy_load_get('bearer_token_prefix')
