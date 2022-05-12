import unittest

from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.util import FileBackedJsonObjectException
from tests.util import tdata_resource_file_path


class TestOidcCredential(unittest.TestCase):

    def test_asserts_valid(self):
        under_test = FileBackedOidcCredential(data=None,
                                              credential_file=tdata_resource_file_path(
                                             'keys/oidc_test_credential.json'))
        under_test.load()
        self.assertIsNotNone(under_test.data())

        with self.assertRaises(FileBackedJsonObjectException):
            under_test.set_data(None)

        with self.assertRaises(FileBackedJsonObjectException):
            under_test.set_data({'test': 'missing all required fields'})

    def test_getters(self):
        under_test = FileBackedOidcCredential(data=None,
                                              credential_file=tdata_resource_file_path(
                                             'keys/oidc_test_credential.json'))
        under_test.load()
        self.assertEqual('_dummy_access_token_', under_test.access_token())
        self.assertEqual('_dummy_refresh_token_', under_test.refresh_token())
        self.assertEqual('_dummy_id_token_', under_test.id_token())
