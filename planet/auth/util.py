import json
import os
import pathlib
import stat
import time

from planet.auth.auth_exception import AuthException


class FileBackedJsonObjectException(AuthException):

    def __init__(self, message=None):
        super().__init__(message)


# TODO: support SOPS encrypted json files. Autodetect SOPS on read.
#    ??? on SOPS write.  This is most useful auth client profile
#    storage, where Client Credential applications have to manage
#    application secrets.
class FileBackedJsonObject:
    """
    A file backed json object for storing information. Base class provides
    lazy loading and validation before saving or setting the data.  Derived
    classes should provide type specific validation and convenience data
    accessors. The intent is that this provide a way to provide an object
    backed by a file, and rails are in place to prevent invalid data from
    being saved or used.

    Data is allowed to be initialized as None, but never set or loaded
    to None.  This is so that JIT load use cases can be supported.
    """

    def __init__(self, data=None, file_path: pathlib.Path = None):
        self._file_path = pathlib.Path(file_path) if file_path else None
        self._load_time = 0
        if data:
            self.check_data(data)
            self._load_time = int(time.time())
        self._data = data

    def path(self) -> pathlib.Path:
        return self._file_path

    def set_path(self, file_path):
        self._file_path = pathlib.Path(file_path) if file_path else None

    def data(self):
        return self._data

    def set_data(self, data):
        self.check_data(data)
        self._data = data
        self._load_time = int(time.time())

    def check_data(self, data):
        """
        Check that the provided data is valid.  Throws an exception if the
        data is not valid. This allows the base class to refuse to store or
        use data, while leaving it to child classes to know what constitutes
        "valid". Child classes should raise FileBackedJsonObjectException
        exception.

        Child classes should override this method as required to do more
        application specific data integrity checks. They should also
        call validation on their base classes so that all layers of
        validation are performed.

        The base assertion is that the data structure has been set.
        It may be empty, but may not be None.
        """
        # Allow empty, but not None
        if not data:
            if data == {}:
                return
            raise FileBackedJsonObjectException(
                "None data is invalid in file " + str(self._file_path))

    def load(self):
        """
        Force a data load from disk.  If the file path has not been set,
        an error will be thrown.  If the loaded data is invalid, an
         will be thrown, and tnged.
        """
        if not self._file_path:
            raise FileBackedJsonObjectException(
                'Cannot load data from file. File path is not set.')

        with open(self._file_path, 'r') as file_r:
            new_data = json.load(file_r)
            self.check_data(new_data)

        self._data = new_data
        self._load_time = int(time.time())

    def save(self):
        if not self._file_path:
            raise FileBackedJsonObjectException(
                'Cannot save data to file. File path is not set.')

        self.check_data(self._data)

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, 'w') as file_w:
            os.chmod(self._file_path, stat.S_IREAD | stat.S_IWRITE)
            file_w.write(json.dumps(self._data))
            self._load_time = int(time.time())

    def lazy_load(self):
        """
        Lazy load the data from disk.

        If the data has already been set, whether by an the constructor, an
        explicit set_data(), or a previous load from disk, no attempt is made
        to refresh the data.  Object will behave as an in memory object.

        If the data is not set, it will attempt to load the data from disk.
        An error will be thrown if the loaded data is invalid, the file has
        not been set, or the file has been set to a non-existent path.

        For updating the data from disk even if an in memory copy exists,
        see lazy_reload().

        Users may always force a load at any time by calling load()
        """
        if not self._data:
            self.load()

    def lazy_reload(self):
        """
        Lazy reload the data from disk.

        If the data is set, a reload will be attempted if the data on disk
        appears to be newer if a path is set.  if a path is not set, no
        attempt will be made to load the data.

        If the data is not set, an error will be thrown if the loaded data is
        invalid, the file has not been set, or the file has been set to a
        non-existent path.
        """
        if not self._data:
            # No data, behave like load()
            self.load()
            return

        if not self._file_path:
            # Have data. No path. Continue with in memory value.
            return

        if int(self._file_path.stat().st_mtime) > self._load_time:
            self.load()

    def lazy_get(self, field):
        self.lazy_load()
        return self._data.get(field)

    # This is probably a bad idea, since it would encourage development
    # that makes it more likely that data may change in between get()'s
    # of multiple fields in the same object, leading to inconsistency.
    # Only the application knows what transation boundaries are.
    # def lazy_reload_get(self, field):
    #    self.lazy_reload()
    #    if self._data:
    #        return self._data.get(field)
    #    return None
