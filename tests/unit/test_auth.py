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


def test_Auth_read_key():
    test_auth = auth.Auth.read(key='test')
    assert test_auth.key == 'test'


def test_Auth_read_env(monkeypatch):
    monkeypatch.setenv('PL_API_KEY', 'a')
    monkeypatch.setenv('OTHER_VAR', 'b')

    test_auth_env1 = auth.Auth.read()
    assert test_auth_env1.key == 'a'

    test_auth_env2 = auth.Auth.read(environment_variable='OTHER_VAR')
    assert test_auth_env2.key == 'b'


def test_Auth_read_file(tmp_path, monkeypatch):
    monkeypatch.delenv('PL_API_KEY')
    secret_path = str(tmp_path / '.test')
    with open(secret_path, 'w') as fp:
        fp.write('{"key": "testvar"}')

    test_auth = auth.Auth.read(secret_file_path=secret_path)
    assert test_auth.key == 'testvar'


def test_Auth_read_error(tmp_path, monkeypatch):
    monkeypatch.delenv('PL_API_KEY')
    secret_path = str(tmp_path / '.test')

    with pytest.raises(auth.AuthException):
        auth.Auth.read(secret_file_path=secret_path)


def test_Auth_write_doesnotexist(tmp_path):
    test_auth = auth.Auth.from_key('test')
    secret_path = str(tmp_path / '.test')
    auth.Auth.write(test_auth, secret_path)

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test"}


def test_Auth_write_exists(tmp_path):
    secret_path = str(tmp_path / '.test')

    with open(secret_path, 'w') as fp:
        fp.write('{"existing": "exists"}')

    test_auth = auth.Auth.from_key('test')
    auth.Auth.write(test_auth, secret_path)

    with open(secret_path, 'r') as fp:
        assert json.loads(fp.read()) == {"key": "test", "existing": "exists"}
