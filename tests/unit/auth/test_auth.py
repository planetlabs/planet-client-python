import pathlib
import unittest

from planet.auth.auth import Auth
from planet.auth.oidc.auth_clients.auth_code_flow import \
    AuthCodePKCEAuthClient
from planet.auth.oidc.request_authenticator import \
    RefreshingOidcTokenRequestAuthenticator
from planet.auth.planet_legacy.auth_client import PlanetLagacyAuthClient
from planet.auth.planet_legacy.request_authenticator import \
    PlanetLegacyRequestAuthenticator
from planet.auth.request_authenticator import \
    SimpleInMemoryRequestAuthenticator
from planet.auth.static_api_key.auth_client import StaticApiKeyAuthClient
from planet.auth.static_api_key.request_authenticator import \
    FileBackedAPIKeyRequestAuthenticator
from tests.util import tdata_resource_file_path


class AuthTest(unittest.TestCase):

    def test_initialize_default_blank(self):
        under_test = Auth.initialize()
        self.assertIsInstance(under_test.auth_client(), AuthCodePKCEAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              RefreshingOidcTokenRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/token.json"),
                         under_test.token_file_path())

    def test_initialize_default_by_profile_name(self):
        under_test = Auth.initialize(profile='default')
        self.assertIsInstance(under_test.auth_client(), AuthCodePKCEAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              RefreshingOidcTokenRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/token.json"),
                         under_test.token_file_path())

    def test_initialize_legacy_by_profile_name(self):
        under_test = Auth.initialize(profile='legacy')
        self.assertIsInstance(under_test.auth_client(), PlanetLagacyAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              PlanetLegacyRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/legacy/token.json"),
            under_test.token_file_path())

    def test_initialize_none_by_profile_name(self):
        under_test = Auth.initialize(profile='none')
        self.assertIsNone(under_test.auth_client())
        self.assertIsInstance(under_test.request_authenticator(),
                              SimpleInMemoryRequestAuthenticator)
        self.assertIsNone(under_test.token_file_path())

    def test_initialize_by_authconffile_valid(self):
        under_test = Auth.initialize(
            profile='test_profile',
            auth_client_config_file=tdata_resource_file_path(
                'auth_client_configs/utest/static_api_key.json'))
        self.assertIsInstance(under_test.auth_client(), StaticApiKeyAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              FileBackedAPIKeyRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/test_profile/token.json"),
            under_test.token_file_path())

    def test_initialize_by_authconffile_valid_fallback_to_default(self):
        under_test = Auth.initialize(profile='test_profile',
                                     auth_client_config_file='__bad_path__')
        self.assertIsInstance(under_test.auth_client(), AuthCodePKCEAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              RefreshingOidcTokenRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(
            # FIXME: is keeping the profile's path what we want when we
            #        use a fallback auth client? Maybe this should just
            #        be a fatal error.
            pathlib.Path.home().joinpath(".planet/test_profile/token.json"),
            under_test.token_file_path())

    def test_default_overides_authconffile(self):
        under_test = Auth.initialize(
            profile='default',
            auth_client_config_file=tdata_resource_file_path(
                'auth_client_configs/utest/static_api_key.json'))
        self.assertIsInstance(under_test.auth_client(), AuthCodePKCEAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              RefreshingOidcTokenRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/token.json"),
                         under_test.token_file_path())

    def test_legacy_overrirdes_authconffile(self):
        under_test = Auth.initialize(
            profile='legacy',
            auth_client_config_file=tdata_resource_file_path(
                'auth_client_configs/utest/static_api_key.json'))
        self.assertIsInstance(under_test.auth_client(), PlanetLagacyAuthClient)
        self.assertIsInstance(under_test.request_authenticator(),
                              PlanetLegacyRequestAuthenticator)
        self.assertIsInstance(under_test.token_file_path(), pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/legacy/token.json"),
            under_test.token_file_path())
