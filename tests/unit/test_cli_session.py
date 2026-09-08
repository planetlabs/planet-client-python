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

import click
import httpx
import respx

import pytest

# from planet.auth import _SecretFile
from planet import auth, http
from planet.cli import session

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
    # The default auth
    async with session.CliSession(
            plsdk_auth=auth.Auth.from_key("clisessiontest")) as sess:
        route = respx.get(TEST_URL)
        route.return_value = httpx.Response(HTTPStatus.OK)

        await sess.request(method='GET', url=TEST_URL)

        # the proper headers are included and they have the expected values
        received_request = route.calls.last.request
        # The planet_auth library sends the api key as bearer token.
        # The older Planet SDK sent it as HTTP basic.
        # Most Planet APIs accept either.
        # credentials = received_request.headers['authorization'].strip(
        #     'Authorization: Basic ')
        # assert base64.b64decode(credentials) == b'clisessiontest:'
        credentials = received_request.headers['authorization']
        assert credentials == 'api-key clisessiontest'


def _click_ctx(**obj):
    """A click context carrying the given context object entries"""
    return click.Context(click.Command('test'), obj=obj)


@pytest.mark.anyio
async def test_CliSession_retry_defaults(test_valid_secretfile):
    """Retry defaults to the module-level configuration"""
    async with session.CliSession() as sess:
        assert sess.max_retries == http.MAX_RETRIES
        assert sess.max_retry_backoff == http.MAX_RETRY_BACKOFF


@pytest.mark.anyio
async def test_CliSession_retry_from_ctx(test_valid_secretfile):
    """Retry configuration is read from the click context"""
    ctx = _click_ctx(PLSDK_AUTH=auth.Auth.from_key("clisessiontest"),
                     MAX_RETRIES=2,
                     MAX_RETRY_BACKOFF=8)

    async with session.CliSession(ctx) as sess:
        assert sess.max_retries == 2
        assert sess.max_retry_backoff == 8


@pytest.mark.anyio
async def test_CliSession_retry_ctx_unset(test_valid_secretfile):
    """Retry falls back to the defaults when the context does not set it"""
    ctx = _click_ctx(PLSDK_AUTH=auth.Auth.from_key("clisessiontest"))

    async with session.CliSession(ctx) as sess:
        assert sess.max_retries == http.MAX_RETRIES
        assert sess.max_retry_backoff == http.MAX_RETRY_BACKOFF
