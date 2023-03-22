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
import json
import logging
from http import HTTPStatus
import math
from unittest.mock import patch

import httpx
import respx

import pytest

from planet import exceptions, http

TEST_URL = 'mock://fantastic.com'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_response():

    def mocker(code, text='', json={"message": "nope"}):
        mock_request = httpx.Request('GET', 'url')
        return httpx.Response(status_code=code,
                              json=json,
                              request=mock_request)

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

    with pytest.raises(exceptions.APIError):
        http.BaseSession._raise_for_status(mock_response(HTTPStatus.FORBIDDEN))

    with pytest.raises(exceptions.APIError):
        http.BaseSession._raise_for_status(
            mock_response(HTTPStatus.METHOD_NOT_ALLOWED, json={}))


@pytest.mark.anyio
async def test__Limiter_max_workers(monkeypatch):
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

    # this value seems small enough to speed up the test but large enough
    # to avoid undue CPU churn
    short_wait = 0.001

    limiter.retry_interval = short_wait

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
                await asyncio.sleep(short_wait)

            active -= 1

    async def control():
        nonlocal active, hold_flag

        # this value seems large enough to allow test functions to start
        # but small enough to not noticeably slow down tests
        await asyncio.sleep(.01)

        # confirm number of workers is capped
        assert active == max_workers

        # release hold so workers can complete
        hold_flag = False

    total_calls = 2 * max_workers  # just needs to be more than worker cap
    test_functions = [test_func() for _ in range(total_calls)]
    await asyncio.gather(*test_functions, control())
    assert calls == total_calls


@pytest.mark.anyio
async def test__Limiter_rate_limit(monkeypatch):
    """Test that the rate limit is enforced.

    This test async queues up tasks and then adjusts the time seen by
    _Limiter, checking that tasks are called according to the rate limit.
    """
    rate_limit = 5  # calls per second
    cadence = .2  # rate of 5/s -> period (cadence) of 200ms
    limiter = http._Limiter(rate_limit=rate_limit, max_workers=0)

    # this value seems small enough to speed up the test but large enough
    # to avoid undue CPU churn
    limiter.retry_interval = 0.001

    # this value seems large enough for one async function to wait for others
    # to progress to the next stage but small enough to not noticeably slow
    # down tests. It needs to be larger than limiter.retry_interval
    other_fcns_wait = 0.01

    # establish control over the time _Limiter reads
    current_time = 0
    monkeypatch.setattr(http._Limiter, '_get_now', lambda x: current_time)

    calls = 0

    async def test_func():
        async with limiter:
            nonlocal calls
            calls += 1

    async def control():
        nonlocal calls, current_time

        # on call gets made right out of the gate
        await asyncio.sleep(other_fcns_wait)
        assert calls == 1

        # we haven't reached cadence delay, no new calls should be made
        current_time = 0.9 * cadence
        await asyncio.sleep(other_fcns_wait)
        assert calls == 1

        # we passed cadence delay, a new call should have been made
        current_time = 1.1 * cadence
        await asyncio.sleep(other_fcns_wait)
        assert calls == 2

        # we skip forward 2 * cadence delay, only one more call should have
        # been made
        current_time = 3.2 * cadence
        await asyncio.sleep(other_fcns_wait)
        assert calls == 3
        LOGGER.debug('here')

        # final call should have been made
        current_time = 5 * cadence
        await asyncio.sleep(other_fcns_wait)
        assert calls == 4

    total_calls = 4  # needs to equal the highest number of calls in control()
    test_functions = [test_func() for _ in range(total_calls)]
    await asyncio.gather(*test_functions, control())


@pytest.mark.anyio
async def test_session_contextmanager():
    async with http.Session():
        pass


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize('data', (None, {'boo': 'baa'}))
async def test_session_request_success(data):

    async with http.Session() as ps:
        resp_json = {'foo': 'bar'}
        route = respx.get(TEST_URL)
        route.return_value = httpx.Response(HTTPStatus.OK, json=resp_json)

        resp = await ps.request(method='GET', url=TEST_URL, json=data)
        assert resp.json() == resp_json

        # the proper headers are included and they have the expected values
        received_request = route.calls.last.request
        assert received_request.headers['x-planet-app'] == 'python-sdk'
        assert 'planet-client-python/' in received_request.headers[
            'user-agent']

        if data:
            assert received_request.headers[
                'content-type'] == 'application/json'
            assert json.loads(received_request.content) == data


@respx.mock
@pytest.mark.anyio
async def test_session_stream():
    async with http.Session() as ps:
        mock_resp = httpx.Response(HTTPStatus.OK, text='bubba')
        respx.get(TEST_URL).return_value = mock_resp

        async with ps.stream(method='GET', url=TEST_URL) as resp:
            chunks = [c async for c in resp.aiter_bytes()]
            assert chunks[0] == b'bubba'


@respx.mock
@pytest.mark.anyio
async def test_session_request_retry():
    """Test the retry in the Session.request method"""
    async with http.Session() as ps:
        route = respx.get(TEST_URL)
        route.side_effect = [
            httpx.Response(HTTPStatus.TOO_MANY_REQUESTS, json={}),
            httpx.Response(HTTPStatus.OK, json={})
        ]

        # let's not actually introduce a wait into the tests
        ps.max_retry_backoff = 0

        resp = await ps.request(method='GET', url=TEST_URL)
        assert resp
        assert route.call_count == 2


@respx.mock
@pytest.mark.anyio
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
@pytest.mark.anyio
async def test_authsession_request():
    sess = http.AuthSession()
    resp_json = {'token': 'foobar'}
    mock_resp = httpx.Response(HTTPStatus.OK, json=resp_json)
    respx.get(TEST_URL).return_value = mock_resp

    resp = sess.request(method='GET', url=TEST_URL, json={'foo': 'bar'})
    assert resp.json() == resp_json


def test_authsession__raise_for_status(mock_response):
    with pytest.raises(exceptions.APIError):
        http.AuthSession._raise_for_status(
            mock_response(HTTPStatus.BAD_REQUEST, json={}))

    with pytest.raises(exceptions.APIError):
        http.AuthSession._raise_for_status(
            mock_response(HTTPStatus.UNAUTHORIZED, json={}))
