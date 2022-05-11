# Copyright 2020 Planet Labs, PBC.
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
import logging
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

import httpx
import respx

import pytest

from planet import exceptions, http

TEST_URL = 'mock://fantastic.com'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_request():
    r = Mock()
    r.http_request = httpx.Request('GET', TEST_URL)
    yield r


@pytest.fixture
def mock_response():

    def mocker(code, text='', json={"message": "nope"}):
        r = Mock()
        r.status_code = code
        r.text = text
        r.json = Mock(return_value=json)
        return r

    return mocker


class AsyncMock(MagicMock):
    """This class was added to the Python library in 3.8"""

    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


def test_basesession__raise_for_status(mock_response):
    http.BaseSession._raise_for_status(
        mock_response(HTTPStatus.CREATED, json={}))

    with pytest.raises(exceptions.BadQuery):
        http.BaseSession._raise_for_status(
            mock_response(HTTPStatus.BAD_REQUEST, json={}))

    with pytest.raises(exceptions.TooManyRequests):
        http.BaseSession._raise_for_status(
            mock_response(HTTPStatus.TOO_MANY_REQUESTS, text='', json={}))

    with pytest.raises(exceptions.OverQuota):
        http.BaseSession._raise_for_status(
            mock_response(HTTPStatus.TOO_MANY_REQUESTS,
                          text='exceeded QUOTA"',
                          json={}))

    with pytest.raises(exceptions.APIError):
        http.BaseSession._raise_for_status(
            mock_response(HTTPStatus.METHOD_NOT_ALLOWED, json={}))


@pytest.mark.asyncio
async def test_session_contextmanager():
    async with http.Session():
        pass


@respx.mock
@pytest.mark.asyncio
async def test_session_request(mock_request):

    async with http.Session() as ps:
        mock_resp = httpx.Response(HTTPStatus.OK, text='bubba')
        respx.get(TEST_URL).return_value = mock_resp

        resp = await ps.request(mock_request)
        assert resp.http_response.text == 'bubba'


@respx.mock
@pytest.mark.asyncio
async def test_session_stream(mock_request):
    async with http.Session() as ps:
        mock_resp = httpx.Response(HTTPStatus.OK, text='bubba')
        respx.get(TEST_URL).return_value = mock_resp

        async with ps.stream(mock_request) as resp:
            txt = await resp.http_response.aread()
            assert txt == b'bubba'


@respx.mock
@pytest.mark.asyncio
async def test_session_request_retry(monkeypatch, mock_request):
    """Test the retry in the Session.request method"""
    async with http.Session() as ps:
        route = respx.get(TEST_URL)
        route.side_effect = [
            httpx.Response(HTTPStatus.TOO_MANY_REQUESTS, json={}),
            httpx.Response(HTTPStatus.OK, json={})
        ]

        # let's not actually introcude a wait into the tests
        monkeypatch.setattr(http, 'MAX_BACKOFF', 0)
        resp = await ps.request(mock_request)
        assert resp
        assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_session__retry(monkeypatch):
    """A unit test for the _retry function"""
    # decorator form of patch seems to conflict with respx.mock
    # if it is placed above respx.mock, the funciton does not seem to be mocked
    # but if it is placed below respx.mock, the reference to the mock cannot
    # be accessed through the test function arguments
    with patch('planet.http.asyncio.sleep',
               new_callable=AsyncMock) as mock_sleep:

        async def test_func():
            raise exceptions.TooManyRequests

        async with http.Session() as ps:
            with pytest.raises(exceptions.TooManyRequests):
                await ps._retry(test_func)

        calls = mock_sleep.call_args_list
        wait_times = [c[0][0] for c in calls]

        # (min, max): 2**n to 2**n + 1
        expected_times = [(2, 3), (4, 5), (8, 9), (16, 17), (32, 33)]

        for wait, expected in zip(wait_times, expected_times):
            assert wait >= expected[0] and wait < expected[1]


@respx.mock
@pytest.mark.asyncio
async def test_authsession_request(mock_request):
    sess = http.AuthSession()
    mock_resp = httpx.Response(HTTPStatus.OK, text='bubba')
    respx.get(TEST_URL).return_value = mock_resp

    resp = sess.request(mock_request)
    assert resp.http_response.text == 'bubba'


def test_authsession__raise_for_status(mock_response):
    with pytest.raises(exceptions.APIError):
        http.AuthSession._raise_for_status(
            mock_response(HTTPStatus.BAD_REQUEST, json={}))

    with pytest.raises(exceptions.APIError):
        http.AuthSession._raise_for_status(
            mock_response(HTTPStatus.UNAUTHORIZED, json={}))
