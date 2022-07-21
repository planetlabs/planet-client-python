# Copyright 2020 Planet Labs, Inc.
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
import asyncio
import logging
from http import HTTPStatus
import math
from unittest.mock import Mock, patch

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
async def test__Limiter_workers(monkeypatch):
    """Test that the worker cap is enforced.

    This test async queues up more tasks than the limiter worker cap. Each task
    registers itself as running, continues to run until an external flag
    is changed, then registers itself as done. Along with the tasks, a
    controller task is run asynchronously. This task waits for the other tasks
    to queue up, checks that the number of tasks running is equal to the
    limiter worker cap, then changes the state of the external flag, releasing
    the tasks.
    """
    max_workers = 2
    limiter = http._Limiter(rate_limit=0, max_workers=max_workers)

    limiter.retry_interval = 0

    active = 0
    calls = 0
    hold_flag = True

    async def test_func():
        async with limiter:
            nonlocal active, calls, hold_flag
            active += 1
            calls += 1

            # wait until hold is released
            while hold_flag:
                await asyncio.sleep(.001)

            active -= 1

    async def control():
        nonlocal active, hold_flag

        # give test functions some time to start
        await asyncio.sleep(.01)

        # confirm number of workers is capped
        assert active == max_workers

        # release hold so workers can complete
        hold_flag = False

    total_calls = 2 * max_workers
    test_functions = [test_func() for _ in range(total_calls)]
    await asyncio.gather(*test_functions, control())
    assert calls == total_calls


@pytest.mark.asyncio
async def test__Limiter_rate_limit(monkeypatch):
    '''Test that function is called at or below rate limit'''
    # current_time = 0
    #
    # def _mock_now(x):
    #     return current_time
    
    _mock_now = Mock()
    _mock_now.side_effect = [.1*n for n in range(100)]

    monkeypatch.setattr(http._Limiter, '_get_now', _mock_now)
    limiter = http._Limiter(rate_limit=5, max_workers=0)
    limiter.retry_interval = 0.000  # speed it up

    calls = []

    LOGGER.warning(limiter._last_call)

    # current_time = 0
    async def _func():
        calls.append(time.time())


    for _ in range(5):
        async with limiter:
            await _func()

    LOGGER.warning(calls)
    assert calls == []


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
async def test_session_request_retry(mock_request):
    """Test the retry in the Session.request method"""
    async with http.Session() as ps:
        route = respx.get(TEST_URL)
        route.side_effect = [
            httpx.Response(HTTPStatus.TOO_MANY_REQUESTS, json={}),
            httpx.Response(HTTPStatus.OK, json={})
        ]

        # let's not actually introduce a wait into the tests
        ps.max_retry_backoff = 0

        resp = await ps.request(mock_request)
        assert resp
        assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_session__retry():
    """A unit test for the _retry function"""

    async def test_func():
        # directly trigger the retry logic
        raise exceptions.TooManyRequests

    with patch('planet.http.Session._calculate_wait') as mock_wait:
        # let's not actually introduce a wait into the tests
        mock_wait.return_value = 0

        async with http.Session() as ps:
            with pytest.raises(exceptions.TooManyRequests):
                await ps._retry(test_func)

        calls = mock_wait.call_args_list
        args = [c[0] for c in calls]
        assert args == [(1, 64), (2, 64), (3, 64), (4, 64), (5, 64)]


def test__calculate_wait():
    max_retry_backoff = 20
    wait_times = [
        http.Session._calculate_wait(i + 1, max_retry_backoff)
        for i in range(5)
    ]

    # (min, max): 2**n to 2**n + 1, last entry hit threshold
    expected_times = [2, 4, 8, 16, 20]

    for wait, expected in zip(wait_times, expected_times):
        # this doesn't really test the randomness but does test exponential
        # and threshold
        assert math.floor(wait) == expected


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
