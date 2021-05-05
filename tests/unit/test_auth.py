# Copyright 2020 Planet Labs, Inc.
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

LOGGER = logging.getLogger(__name__)


def test_APIKey_init():
    with pytest.raises(auth.APIKeyException):
        key = auth.APIKey('')

    key = auth.APIKey('mockkey')
    assert key._val == 'mockkey'


def test_APIKey_from_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'a')
    monkeypatch.setenv('OTHER_VAR', 'b')

    key = auth.APIKey.from_env('PL_API_KEY')
    assert key._val == 'a'

    key = auth.APIKey.from_env('OTHER_VAR')
    assert key._val == 'b'


def test_APIKey_from_dict():
    test_dict = {'key': 'test_key'}

    key = auth.APIKey.from_dict(test_dict)
    assert key._val == 'test_key'


def test_APIKey_to_dict():
    key = auth.APIKey(key='test_key')
    assert key.to_dict() == {'key': 'test_key'}


def test_APIKey_header():
    key = auth.APIKey(key='test_key')
    assert key.header() == {'Authorization': 'api-key test_key'}


def test_SecretFile_write(tmp_path):
    secret_path = str(tmp_path / '.test')
    contents = {'testkey': 'testvar'}
    auth.SecretFile(secret_path).write(contents)

    with open(secret_path, 'r') as fp:
        assert fp.read() == '{"testkey": "testvar"}'


def test_SecretFile_read(tmp_path):
    secret_path = str(tmp_path / '.test')

    with open(secret_path, 'w') as fp:
        fp.write('{"testkey": "testvar"}')

    contents = auth.SecretFile(secret_path).read()
    assert contents == {'testkey': 'testvar'}


def test_Auth_init_key():
    test_auth = auth.Auth(key='test')
    assert test_auth._auth._val == 'test'


def test_Auth_init_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'a')
    monkeypatch.setenv('OTHER_VAR', 'b')

    test_auth_env1 = auth.Auth()
    assert test_auth_env1._auth._val == 'a'

    test_auth_env2 = auth.Auth(environment_variable='OTHER_VAR')
    assert test_auth_env2._auth._val == 'b'


def test_Auth_init_secretfile(tmp_path, monkeypatch):
    monkeypatch.delenv('PL_API_KEY')
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar"}')

    test_auth = auth.Auth(secret_file_path=secret_path)
    assert test_auth._auth._val == 'testvar'


def test_Auth_init_error(tmp_path, monkeypatch):
    monkeypatch.delenv('PL_API_KEY')
    secret_path = str(tmp_path / '.test')

    with pytest.raises(auth.AuthException):
        auth.Auth(secret_file_path=secret_path)


def test_Auth_store_doesnotexist(tmp_path):
    secret_path = str(tmp_path / '.test')
    test_auth = auth.Auth(key='test', secret_file_path=secret_path)
    test_auth.store()

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test"}


def test_Auth_store_exists(tmp_path):
    secret_path = str(tmp_path / '.test')
    test_auth = auth.Auth(key='test', secret_file_path=secret_path)

    with open(secret_path, 'w') as fp:
        fp.write('{"existing": "exists"}')

    test_auth.store()

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test", "existing": "exists"}


def test_Auth_header():
    test_auth = auth.Auth(key='test')
    assert test_auth.header() == {'Authorization': 'api-key test'}
