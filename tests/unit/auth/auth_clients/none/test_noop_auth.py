import pathlib
import unittest

from planet.auth.none.noop_auth import NoOpCredential, NoOpAuthClientConfig, \
    NoOpAuthClient

TEST_CREDENTIAL_FILE = "/some/path/that/does/not/exist.json"


class NoOpCredentialTest(unittest.TestCase):

    def test_noop_cred(self):
        under_test = NoOpCredential()
        under_test.set_path(TEST_CREDENTIAL_FILE)

        under_test.load()  # Should do nothing.

        under_test.save()
        self.assertFalse(pathlib.Path(TEST_CREDENTIAL_FILE).exists())


class NoOpAuthClientTest(unittest.TestCase):

    def setUp(self):
        self.under_test = NoOpAuthClient(NoOpAuthClientConfig())

    def test_login(self):
        cred = self.under_test.login()
        self.assertIsInstance(cred, NoOpCredential)

    def test_refresh(self):
        cred = self.under_test.refresh("refresh_token", requested_scopes=[])
        self.assertIsInstance(cred, NoOpCredential)

    def test_validate_access_token(self):
        results = self.under_test.validate_access_token("test_token")
        self.assertEqual({}, results)

    def test_validate_id_token(self):
        results = self.under_test.validate_id_token("test_token")
        self.assertEqual({}, results)

    def test_validate_id_token_local(self):
        results = self.under_test.validate_id_token_local("test_token")
        self.assertEqual({}, results)

    def test_validate_refresh_token(self):
        results = self.under_test.validate_refresh_token("test_token")
        self.assertEqual({}, results)

    def test_revoke_access_token(self):
        # test passes if it doesn't raise an exception
        self.under_test.revoke_access_token("test_token")

    def test_revoke_refresh_token(self):
        # test passes if it doesn't raise an exception
        self.under_test.revoke_refresh_token("test_token")

    def test_get_scopes(self):
        results = self.under_test.get_scopes()
        self.assertEqual([], results)
