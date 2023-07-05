# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
from http import HTTPStatus
import json
import os

from click.testing import CliRunner
import httpx
import jwt
import pytest
import respx

from planet.cli import cli

TEST_URL = 'http://MockNotRealURL/api/path'
TEST_LOGIN_URL = f'{TEST_URL}/login'


# skip the global mock of _SecretFile.read
# for this module
@pytest.fixture(autouse=True, scope='module')
def test_secretfile_read():
    return


@pytest.fixture
def redirect_secretfile(tmp_path):
    """patch the cli so it works with a temporary secretfile

    this is to avoid collisions with the actual planet secretfile
    """
    secretfile_path = tmp_path / 'secret.json'

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(cli.auth.planet.auth, 'SECRET_FILE_PATH', secretfile_path)
        yield secretfile_path


@respx.mock
def test_cli_auth_init_success(redirect_secretfile):
    """Test the successful auth init path

    Also tests the base-url command, since we will get an exception
    if the base url is not changed to the mocked url
    """
    payload = {'api_key': 'test_cli_auth_init_success_key'}
    resp = {'token': jwt.encode(payload, 'key')}
    mock_resp = httpx.Response(HTTPStatus.OK, json=resp)
    respx.post(TEST_LOGIN_URL).return_value = mock_resp

    result = CliRunner().invoke(cli.main,
                                args=['auth', '--base-url', TEST_URL, 'init'],
                                input='email\npw\n')

    # we would get a 'url not mocked' exception if the base url wasn't
    # changed to the mocked url
    assert not result.exception

    assert 'Initialized' in result.output


@respx.mock
def test_cli_auth_init_bad_pw(redirect_secretfile):
    resp = {
        "errors": None,
        "message": "Invalid email or password",
        "status": 401,
        "success": False
    }
    mock_resp = httpx.Response(401, json=resp)
    respx.post(TEST_LOGIN_URL).return_value = mock_resp

    result = CliRunner().invoke(cli.main,
                                args=['auth', '--base-url', TEST_URL, 'init'],
                                input='email\npw\n')

    assert result.exception
    assert 'Error: Incorrect email or password.\n' in result.output


def test_cli_auth_value_success(redirect_secretfile):
    key = 'test_cli_auth_value_success_key'
    content = {'key': key}
    with open(redirect_secretfile, 'w') as f:
        json.dump(content, f)

    result = CliRunner().invoke(cli.main, ['auth', 'value'])
    assert not result.exception
    assert result.output == f'{key}\n'


def test_cli_auth_value_failure(redirect_secretfile):
    result = CliRunner().invoke(cli.main, ['auth', 'value'])
    assert result.exception
    assert 'Error: Auth information does not exist or is corrupted.' \
        in result.output


def test_cli_auth_store_cancel(redirect_secretfile):
    result = CliRunner().invoke(cli.main, ['auth', 'store', 'setval'],
                                input='')
    assert not result.exception
    assert not os.path.isfile(redirect_secretfile)


def test_cli_auth_store_confirm(redirect_secretfile):
    result = CliRunner().invoke(cli.main, ['auth', 'store', 'setval'],
                                input='y')
    assert not result.exception

    with open(redirect_secretfile, 'r') as f:
        assert json.load(f) == {'key': 'setval'}
