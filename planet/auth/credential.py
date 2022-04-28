from planet.auth.util import FileBackedJsonObject


# FIXME: The relationship here is probably upside-down.  Not all credentials
#        need be file backed.
class Credential(FileBackedJsonObject):

    def __init__(self, data=None, file_path=None):
        super().__init__(data=data, file_path=file_path)
