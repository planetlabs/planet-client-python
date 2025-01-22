# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

import pytest

import planet.auth
from planet import auth
import planet_auth

import planet.auth_builtins
from planet.auth_builtins import PlanetOAuthScopes

LOGGER = logging.getLogger(__name__)


# skip the global mock of _SecretFile.read
# for this module
@pytest.fixture(autouse=True, scope='module')
def test_secretfile_read():
    return


@pytest.fixture
def secret_path(monkeypatch, tmp_path):
    secret_path = tmp_path / '.test'
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)
    yield secret_path


def test_Auth_from_key():
    test_auth_env1 = auth.Auth.from_key('testkey_from_key')
    # We know that planet_auth instantiates an in memory "static API key" auth client.
    # test_api_key = test_auth_env1._plauth.request_authenticator().credential().legacy_api_key()
    test_api_key = test_auth_env1._plauth.request_authenticator().credential(
    ).api_key()
    assert test_api_key == 'testkey_from_key'


def test_Auth_from_key_empty():
    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_key('')


def test_Auth_from_file(secret_path):
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar_from_file"}')

    test_auth = auth.Auth.from_file()
    # We know that planet_auth instantiates a "Legacy" auth client.
    test_api_key = test_auth._plauth.request_authenticator().credential(
    ).legacy_api_key()
    # test_api_key = test_auth._plauth.request_authenticator().credential().api_key()
    assert test_api_key == 'testvar_from_file'


def test_Auth_from_file_doesnotexist(secret_path):
    test_auth = auth.Auth.from_file(secret_path)
    with pytest.raises(FileNotFoundError):
        _ = test_auth._plauth.request_authenticator().credential(
        ).legacy_api_key()


def test_Auth_from_file_wrongformat(secret_path):
    with open(secret_path, 'w') as fp:
        fp.write('{"notkey": "testvar_wrong_format"}')
    test_auth = auth.Auth.from_file(secret_path)
    with pytest.raises(planet_auth.InvalidDataException):
        _ = test_auth._plauth.request_authenticator().credential(
        ).legacy_api_key()


def test_Auth_from_file_alternate(tmp_path):
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar_alt_path"}')

    test_auth = auth.Auth.from_file(secret_path)
    test_api_key = test_auth._plauth.request_authenticator().credential(
    ).legacy_api_key()
    assert test_api_key == 'testvar_alt_path'


def test_Auth_from_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'testkey_env')
    test_auth_env = auth.Auth.from_env()
    # TODO: that I short cicuit between legacy and API key auth impls makes this weird.
    test_api_key = test_auth_env._plauth.request_authenticator().credential(
    ).api_key()
    assert test_api_key == 'testkey_env'


def test_Auth_from_env_failure(monkeypatch):
    monkeypatch.delenv('PL_API_KEY', raising=False)
    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_env()


def test_Auth_from_env_alternate_success(monkeypatch):
    alternate = 'OTHER_VAR'
    monkeypatch.setenv(alternate, 'testkey')
    monkeypatch.delenv('PL_API_KEY', raising=False)

    test_auth_env = auth.Auth.from_env(alternate)
    test_api_key = test_auth_env._plauth.request_authenticator().credential(
    ).api_key()

    assert test_api_key == 'testkey'


def test_Auth_from_env_alternate_doesnotexist(monkeypatch):
    alternate = 'OTHER_VAR'
    monkeypatch.delenv(alternate, raising=False)
    monkeypatch.delenv('PL_API_KEY', raising=False)

    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_env(alternate)


def test_Auth_from_login(monkeypatch):
    # auth.AuthClient has been completely removed
    # in the conversion to planet_auth
    # def login(*args, **kwargs):
    #     return {'api_key': auth_data}
    #
    # monkeypatch.setattr(auth.AuthClient, 'login', login)
    with pytest.raises(DeprecationWarning):
        _ = auth.Auth.from_login('email', 'pw')


def test_Auth_from_user_defaults():
    # The primary implementation is implemented and unit tested by the planet auth libraries.
    # This tests that it doesn't explode with an exception.
    # CI/CD currently is run by configuring auth via PL_API_KEY env var.
    # What this will actually do in an user env depends on a lot of variables.
    _ = auth.Auth.from_user_defaults()


def test_Auth_from_oauth_m2m():
    under_test = auth.Auth.from_oauth_m2m(
        "mock_client_id__from_oauth_m2m", "mock_client_secret__from_oauth_m2m")
    assert isinstance(under_test, planet.auth._PLAuthLibAuth)
    assert isinstance(under_test._plauth.auth_client(),
                      planet_auth.ClientCredentialsClientSecretAuthClient)

    assert under_test._plauth.auth_client()._ccauth_client_config.auth_server(
    ) == planet.auth_builtins._ProductionEnv.OAUTH_AUTHORITY_M2M["auth_server"]

    assert under_test._plauth.auth_client()._ccauth_client_config.client_id(
    ) == "mock_client_id__from_oauth_m2m"

    assert under_test._plauth.auth_client(
    )._ccauth_client_config.client_secret(
    ) == "mock_client_secret__from_oauth_m2m"


def test_Auth_from_oauth_user_session():
    under_test = auth.Auth.from_oauth_user_session()
    assert isinstance(under_test, planet.auth._PLAuthLibAuth)
    assert isinstance(under_test._plauth.auth_client(),
                      planet_auth.DeviceCodeAuthClient)

    assert under_test._plauth.auth_client(
    )._devicecode_client_config.auth_server(
    ) == planet.auth_builtins._ProductionEnv.OAUTH_AUTHORITY_USER[
        "auth_server"]

    assert under_test._plauth.auth_client(
    )._devicecode_client_config.client_id(
    ) == planet.auth_builtins._SDK_CLIENT_ID_PROD


def test_Auth_from_oauth_client_config():
    under_test = auth.Auth.beta_from_oauth_client_config(
        client_id="mock_client_id__from_oauth_config",
        requested_scopes=[
            PlanetOAuthScopes.PLANET, PlanetOAuthScopes.OFFLINE_ACCESS
        ],
        save_token_file=False)

    assert isinstance(under_test, planet.auth._PLAuthLibAuth)
    assert isinstance(under_test._plauth.auth_client(),
                      planet_auth.DeviceCodeAuthClient)

    assert under_test._plauth.auth_client(
    )._devicecode_client_config.auth_server(
    ) == planet.auth_builtins._ProductionEnv.OAUTH_AUTHORITY_USER[
        "auth_server"]

    assert under_test._plauth.auth_client(
    )._devicecode_client_config.client_id(
    ) == "mock_client_id__from_oauth_config"


def test_auth_value_deprecated():
    with pytest.raises(DeprecationWarning):
        test_auth = auth.Auth.from_key("test_deprecated_key")
        _ = test_auth.value


def test_auth_store_deprecated():
    with pytest.raises(DeprecationWarning):
        test_auth = auth.Auth.from_key("test_deprecated_key")
        test_auth.store()


def test_auth_to_dict_deprecated():
    with pytest.raises(DeprecationWarning):
        test_auth = auth.Auth.from_key("test_deprecated_key")
        _ = test_auth.to_dict()


def test_auth_from_dict_deprecated():
    with pytest.raises(DeprecationWarning):
        _ = auth.Auth.from_dict({})
