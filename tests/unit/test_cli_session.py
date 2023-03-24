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
import base64
from http import HTTPStatus
import json

import httpx
import respx

import pytest

# from planet.auth import _SecretFile
from planet import auth
from planet.cli import session
from planet.exceptions import AuthException

TEST_URL = 'mock://mock.com'


# skip the global mock of _SecretFile.read
# for this module
@pytest.fixture(autouse=True, scope='module')
def test_secretfile_read():
    return


@pytest.fixture()
def test_valid_secretfile(tmp_path, monkeypatch):
    # write our own secret file
    secret_path = f'{tmp_path}/secret.test'
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)
    with open(secret_path, 'w') as fp:
        json.dump({'key': 'clisessiontest'}, fp)


@respx.mock
@pytest.mark.anyio
async def test_CliSession_headers(test_valid_secretfile):
    async with session.CliSession() as sess:
        route = respx.get(TEST_URL)
        route.return_value = httpx.Response(HTTPStatus.OK)

        await sess.request(method='GET', url=TEST_URL)

        # the proper headers are included and they have the expected values
        received_request = route.calls.last.request
        assert received_request.headers['x-planet-app'] == 'python-cli'
        assert 'planet-client-python/' in received_request.headers[
            'user-agent']


@respx.mock
@pytest.mark.anyio
async def test_CliSession_auth_valid(test_valid_secretfile):
    async with session.CliSession() as sess:
        route = respx.get(TEST_URL)
        route.return_value = httpx.Response(HTTPStatus.OK)

        await sess.request(method='GET', url=TEST_URL)

        # the proper headers are included and they have the expected values
        received_request = route.calls.last.request
        credentials = received_request.headers['authorization'].strip(
            'Authorization: Basic ')
        assert base64.b64decode(credentials) == b'clisessiontest:'


@respx.mock
@pytest.mark.anyio
async def test_CliSession_auth_invalid(tmp_path, monkeypatch):
    # write invalid secret file
    secret_path = f'{tmp_path}/secret.test'
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)
    with open(secret_path, 'w') as fp:
        json.dump({'invalidkey': 'clisessiontest'}, fp)

    with pytest.raises(AuthException):
        session.CliSession()


@respx.mock
@pytest.mark.anyio
async def test_CliSession_auth_nofile(tmp_path, monkeypatch):
    # point to non-existant file
    secret_path = f'{tmp_path}/doesnotexist.test'
    monkeypatch.setattr(auth, 'SECRET_FILE_PATH', secret_path)

    with pytest.raises(AuthException):
        session.CliSession()
