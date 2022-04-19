import json
import os
import pathlib
import stat
import time


class FileBackedJsonObjectException(Exception):
    def __init__(self, message=None):
        super().__init__(message)


# TODO: support SOPS encrypted json files. Autodetect on read. ??? on write.
class FileBackedJsonObject:
    """
    A file backed json object for storing information. Base class provides lazy loading and validation before
    saving the data.  Derived classes should provide type specific validation and convenience data accessors.
    """
    def __init__(self, data=None, file_path: pathlib.Path = None):
        self._data = data
        self._file_path = pathlib.Path(file_path) if file_path else None
        self._load_time = 0

    def path(self) -> pathlib.Path:
        return self._file_path

    def set_path(self, file_path):
        self._file_path = pathlib.Path(file_path) if file_path else None

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data

    def assert_valid(self):
        """
        Check if the stored data is valid.  Throws an exception if the
        data is not valid. This allows the base class to refuse to store or use
        data, while leaving it to child classes to know what constitutes "valid".
        Child classes should raise FileBackedJsonObjectException exception.

        Child classes should override this method as required to do more application
        specific data integrity checks.
        """
        if not self._data:
            raise FileBackedJsonObjectException(
                "Data has not been successfully loaded from " + str(self._file_path))

    def load(self):
        if not self._file_path:
            raise FileBackedJsonObjectException('Cannot load data from file. File path is not set.')
        # Open to debate if this is best, but if there is a failure, the _data reflects this by being empty.
        # This forces repeated lazy loads to retry.  Alternatively, we could throw and leave data as-is, but then
        # lazy load would not retry, only explicit loads would.
        self._data = None
        with open(self._file_path, 'r') as file_r:
            self._data = json.load(file_r)
            self._load_time = int(time.time())

    def save(self):
        if not self._file_path:
            raise FileBackedJsonObjectException('Cannot save data to file. File path is not set.')
        self.assert_valid()

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, 'w') as token_file_w:
            os.chmod(self._file_path, stat.S_IREAD | stat.S_IWRITE)
            token_file_w.write(json.dumps(self._data))
            # Add a few seconds of wiggle room to sync the file and not trigger a reload.
            self._load_time = int(time.time() + 5)

    def lazy_load(self):
        if not self._data:
            self.load()

    def lazy_reload(self):
        if not self._file_path:
            raise FileBackedJsonObjectException('Cannot load data from file. File path is not set.')
        if int(self._file_path.stat().st_mtime) > self._load_time:
            self.load()

    def lazy_load_get(self, field):
        self.lazy_load()
        if self._data:
            return self._data.get(field)
        return None

    # We may not want to reload in the middle of a transaction that needs to get multiple fields.
    # It's up to the user to know when to user a lazy load vs lazy reload.
    def lazy_reload_get(self, field):
        self.lazy_reload()
        if self._data:
            return self._data.get(field)
        return None
