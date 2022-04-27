from planet.auth.credential import Credential
from planet.auth.util import FileBackedJsonObjectException


class FileBackedOidcToken(Credential):

    def __init__(self, data=None, token_file=None):
        super().__init__(data=data, file_path=token_file)

    def assert_valid(self):
        super().assert_valid()
        if (not self._data.get('access_token')
                and not self._data.get('id_token')
                and not self._data.get('refresh_token')):
            raise FileBackedJsonObjectException(
                "'access_token', 'id_token', or 'refresh_token'"
                " not found in file " + str(self._file_path))

    def access_token(self):
        return self.lazy_load_get('access_token')

    def id_token(self):
        return self.lazy_load_get('id_token')

    def refresh_token(self):
        return self.lazy_load_get('refresh_token')
