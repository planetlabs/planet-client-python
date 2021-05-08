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
# from unittest.mock import patch

import pytest

from planet import auth

LOGGER = logging.getLogger(__name__)


def test_Auth_read_key():
    test_auth = auth.Auth.read(key='test')
    assert test_auth.key == 'test'


def test_Auth_read_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'a')

    test_auth_env1 = auth.Auth.read()
    assert test_auth_env1.key == 'a'


def test_Auth_read_file(tmp_path, monkeypatch):
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar"}')

    monkeypatch.delenv('PL_API_KEY', raising=False)
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)
    test_auth = auth.Auth.read()
    assert test_auth.key == 'testvar'


def test_Auth_read_error(tmp_path, monkeypatch):
    secret_path = str(tmp_path / '.doesnotexist')

    monkeypatch.delenv('PL_API_KEY', raising=False)
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)
    with pytest.raises(auth.AuthException):
        auth.Auth.read()


def test_Auth_from_key_empty():
    with pytest.raises(auth.APIKeyAuthException):
        _ = auth.Auth.from_key('')


def test_Auth_from_file_alternate_success(tmp_path):
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar"}')

    test_auth = auth.Auth.from_file(secret_path)
    assert test_auth.key == 'testvar'


def test_Auth_from_file_alternate_doesnotexist(tmp_path):
    secret_path = str(tmp_path / '.doesnotexist')
    with pytest.raises(auth.AuthException):
        _ = auth.Auth.from_file(secret_path)


def test_Auth_from_file_alternate_wrongformat(tmp_path):
    secret_path = str(tmp_path / '.wrongformat')
    with open(secret_path, 'w') as fp:
        fp.write('{"notkey": "testvar"}')

    with pytest.raises(auth.AuthException):
        _ = auth.Auth.from_file(secret_path)


def test_Auth_from_env_alternate_success(monkeypatch):
    alternate = 'OTHER_VAR'
    monkeypatch.setenv(alternate, 'testkey')
    monkeypatch.delenv('PL_API_KEY', raising=False)

    test_auth_env1 = auth.Auth.from_env(alternate)
    assert test_auth_env1.key == 'testkey'


def test_Auth_from_env_alternate_doesnotexist(monkeypatch):
    alternate = 'OTHER_VAR'
    monkeypatch.delenv(alternate, raising=False)
    monkeypatch.delenv('PL_API_KEY', raising=False)

    with pytest.raises(auth.AuthException):
        _ = auth.Auth.from_env(alternate)


def test_Auth_write_doesnotexist(tmp_path):
    test_auth = auth.Auth.from_key('test')
    secret_path = str(tmp_path / '.test')
    test_auth.write(secret_path)

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test"}


def test_Auth_write_exists(tmp_path):
    secret_path = str(tmp_path / '.test')

    with open(secret_path, 'w') as fp:
        fp.write('{"existing": "exists"}')

    test_auth = auth.Auth.from_key('test')
    test_auth.write(secret_path)

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test", "existing": "exists"}
