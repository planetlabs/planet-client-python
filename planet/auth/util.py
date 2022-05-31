import json
import os
import pathlib
import stat
import subprocess
import time

from planet.auth.auth_exception import AuthException


def parse_content_type(content_type: str):
    result = {
        'content-type': None,
    }
    if content_type:
        ct = content_type.split(';')
        result['content-type'] = ct.pop(0).strip()
        if not result['content-type']:
            # Don't return blank strings
            result['content-type'] = None
        for subfield in ct:
            sf = subfield.split('=', 1)
            if sf[0].strip():
                if len(sf) == 1:
                    result[sf[0].strip()] = None
                else:
                    result[sf[0].strip()] = sf[1].strip()
    return result


class FileBackedJsonObjectException(AuthException):

    def __init__(self, message=None):
        super().__init__(message)


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

        if self._is_sops_path(self._file_path):
            new_data = self._read_json_sops(self._file_path)
        else:
            new_data = self._read_json(self._file_path)

        self.check_data(new_data)

        self._data = new_data
        self._load_time = int(time.time())

    def save(self):
        if not self._file_path:
            raise FileBackedJsonObjectException(
                'Cannot save data to file. File path is not set.')

        self.check_data(self._data)

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if self._is_sops_path(self._file_path):
            self._write_json_sops(self._file_path, self._data)
        else:
            self._write_json(self._file_path, self._data)

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
    # Only the application knows what transaction boundaries are.
    # def lazy_reload_get(self, field):
    #    self.lazy_reload()
    #    if self._data:
    #        return self._data.get(field)
    #    return None

    @staticmethod
    def _read_json(data_file):
        with open(data_file, 'r') as file_r:
            return json.load(file_r)

    @staticmethod
    def _read_json_sops(data_file):
        data_b = subprocess.check_output(['sops', '-d', data_file])
        return json.loads(data_b)

    @staticmethod
    def _write_json(data_file, data):
        with open(data_file, 'w') as file_w:
            os.chmod(data_file, stat.S_IREAD | stat.S_IWRITE)
            file_w.write(json.dumps(data))

    @staticmethod
    def _write_json_sops(data_file, data):
        # TODO: It would be nice to only encrypt the fields we need to.
        #       It would be a better user experience.  Probably the thing to
        #       do is let derived classes tell us what fields are to
        #       be encrypted.
        # Seems to blow up. I guess we have to write clear text,
        # then encrypt in place?
        # with io.StringIO(json.dumps(data)) as data_f:
        #     subprocess.check_call(
        #         ['sops', '-e', '--input-type', 'json', '--output-type',
        #          'json', '--output', data_file, '/dev/stdin'],
        #         stdin=data_f)
        FileBackedJsonObject._write_json(data_file, data)
        subprocess.check_call([
            'sops',
            '-e',
            '--input-type',
            'json',
            '--output-type',
            'json',
            '-i',
            data_file
        ])

    @staticmethod
    def _is_sops_path(file_path):
        # FIXME: could be json.sops, or sops.json, depending on file
        #        level or field level encryption.  We currently only
        #        look for and support field level encryption in json files.
        return bool(file_path.suffixes == ['.sops', '.json'])
