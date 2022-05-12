from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException


class FileBackedApiKey(Credential):

    def __init__(self, api_key=None, prefix='Bearer', api_key_file=None):
        if api_key:
            init_data = {'api_key': api_key, 'bearer_token_prefix': prefix}
        else:
            init_data = None

        super().__init__(data=init_data, file_path=api_key_file)

    def check_data(self, data):
        super().check_data(data)
        if not data.get('api_key'):
            raise FileBackedJsonObjectException(
                "'api_key' not found in file " + str(self._file_path))
        if not data.get('bearer_token_prefix'):
            raise FileBackedJsonObjectException(
                "'bearer_token_prefix' not found in file " +
                str(self._file_path))

    def api_key(self):
        return self.lazy_get('api_key')

    def bearer_token_prefix(self):
        return self.lazy_get('bearer_token_prefix')
