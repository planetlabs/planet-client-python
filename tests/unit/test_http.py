# Copyright 2020 Planet Labs, Inc.
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
from unittest.mock import Mock

import httpx
import respx

import pytest

from planet.api import exceptions, http


TEST_URL = 'mock://fantastic.com'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_request():
    r = Mock()
    r.http_request = httpx.Request(
        'GET',
        TEST_URL)
    yield r


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


@pytest.mark.asyncio
async def test_session__raise_for_status():
    await http.Session._raise_for_status(Mock(
        status_code=HTTPStatus.CREATED, text=''
    ))

    with pytest.raises(exceptions.BadQuery):
        await http.Session._raise_for_status(Mock(
            status_code=HTTPStatus.BAD_REQUEST, text=''
        ))

    with pytest.raises(exceptions.TooManyRequests):
        await http.Session._raise_for_status(Mock(
            status_code=HTTPStatus.TOO_MANY_REQUESTS, text=''
        ))

    with pytest.raises(exceptions.OverQuota):
        await http.Session._raise_for_status(Mock(
            status_code=HTTPStatus.TOO_MANY_REQUESTS, text='exceeded QUOTA'
        ))


@respx.mock
@pytest.mark.asyncio
async def test_session_request_retry(mock_request):
    async with http.Session() as ps:
        route = respx.get(TEST_URL)
        route.side_effect = [
            httpx.Response(HTTPStatus.TOO_MANY_REQUESTS),
            httpx.Response(HTTPStatus.OK)
        ]

        ps.retry_wait_time = 0  # lets not slow down tests for this
        resp = await ps.request(mock_request)
        assert resp
        assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_session_retry(mock_request):
    async with http.Session() as ps:
        async def test_func():
            raise exceptions.TooManyRequests

        ps.retry_wait_time = 0
        with pytest.raises(http.SessionException):
            await ps.retry(test_func)
