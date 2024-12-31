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
import json
import logging

import pytest

from planet import auth
import planet_auth

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
    test_api_key = test_auth_env1._plauth.request_authenticator().credential().api_key()
    assert test_api_key == 'testkey_from_key'


def test_Auth_from_key_empty():
    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_key('')


def test_Auth_from_file(secret_path):
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar_from_file"}')

    test_auth = auth.Auth.from_file()
    # We know that planet_auth instantiates a "Legacy" auth client.
    test_api_key = test_auth._plauth.request_authenticator().credential().legacy_api_key()
    # test_api_key = test_auth._plauth.request_authenticator().credential().api_key()
    assert test_api_key == 'testvar_from_file'


def test_Auth_from_file_doesnotexist(secret_path):
    test_auth = auth.Auth.from_file(secret_path)
    with pytest.raises(FileNotFoundError):
        _ = test_auth._plauth.request_authenticator().credential().legacy_api_key()

def test_Auth_from_file_wrongformat(secret_path):
    with open(secret_path, 'w') as fp:
        fp.write('{"notkey": "testvar_wrong_format"}')
    test_auth = auth.Auth.from_file(secret_path)
    with pytest.raises(planet_auth.InvalidDataException):
        _ = test_auth._plauth.request_authenticator().credential().legacy_api_key()



def test_Auth_from_file_alternate(tmp_path):
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar_alt_path"}')

    test_auth = auth.Auth.from_file(secret_path)
    test_api_key = test_auth._plauth.request_authenticator().credential().legacy_api_key()
    assert test_api_key == 'testvar_alt_path'


def test_Auth_from_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'testkey_env')
    test_auth_env = auth.Auth.from_env()
    # TODO: that I short cicuit between legacy and API key auth impls makes this weird.
    test_api_key = test_auth_env._plauth.request_authenticator().credential().api_key()
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
    test_api_key = test_auth_env._plauth.request_authenticator().credential().api_key()

    assert test_api_key == 'testkey'


def test_Auth_from_env_alternate_doesnotexist(monkeypatch):
    alternate = 'OTHER_VAR'
    monkeypatch.delenv(alternate, raising=False)
    monkeypatch.delenv('PL_API_KEY', raising=False)

    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_env(alternate)


def test_Auth_from_login(monkeypatch):
    auth_data = 'authdata'

    # auth.AuthClient has been completely removed
    # in the conversion to planet_auth
    # def login(*args, **kwargs):
    #     return {'api_key': auth_data}
    #
    # monkeypatch.setattr(auth.AuthClient, 'login', login)
    with pytest.raises(DeprecationWarning):
        test_auth = auth.Auth.from_login('email', 'pw')


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
