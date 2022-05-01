import unittest

from planet.auth.oidc.auth_clients.resource_owner_flow import \
    ResourceOwnerClientConfig, ResourceOwnerAuthClient

TEST_AUTH_SERVER = 'https://blackhole.unittest.planet.com/fake_authserver'
TEST_CLIENT_ID = 'fake_test_client_id'


class ResourceOwnerFlowTest(unittest.TestCase):

    def setUp(self):
        self.under_test = ResourceOwnerAuthClient(
            ResourceOwnerClientConfig(auth_server=TEST_AUTH_SERVER,
                                      client_id=TEST_CLIENT_ID))

    def test_placeholder(self):
        # Dummy fake test since there is no real implementation yet.
        # this is here just to not let the stub class fail test coverage
        # requirements.
        with self.assertRaises(Exception):
            self.under_test.login()
        with self.assertRaises(Exception):
            self.under_test._client_auth_enricher(None, None)
        with self.assertRaises(Exception):
            self.under_test.default_request_authenticator(None)
