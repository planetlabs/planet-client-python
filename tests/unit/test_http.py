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
    http.BaseSession._raise_for_status(mock_response(
        HTTPStatus.CREATED,
        json={}
    ))

    with pytest.raises(exceptions.BadQuery):
        http.BaseSession._raise_for_status(mock_response(
            HTTPStatus.BAD_REQUEST,
            json={}
        ))

    with pytest.raises(exceptions.TooManyRequests):
        http.BaseSession._raise_for_status(mock_response(
            HTTPStatus.TOO_MANY_REQUESTS,
            text='',
            json={}
        ))

    with pytest.raises(exceptions.OverQuota):
        http.BaseSession._raise_for_status(mock_response(
            HTTPStatus.TOO_MANY_REQUESTS,
            text='exceeded QUOTA"',
            json={}
        ))

    with pytest.raises(exceptions.APIException):
        http.BaseSession._raise_for_status(mock_response(
            HTTPStatus.METHOD_NOT_ALLOWED,
            json={}
        ))


def test_basesession__parse_message(mock_response):
    create_order_bad_id_msg = {
        "field": {
            "Details": [
                {"message": "Item ID 1 / Item Type PSScene3Band doesn't exist"}
            ]
        },
        "general": [
            {"message": "Unable to accept order"}
        ]
    }

    msg = http.BaseSession._parse_message(mock_response(
            HTTPStatus.BAD_REQUEST,
            json=create_order_bad_id_msg
        ))
    assert msg == (
        "Unable to accept order - " +
        "Item ID 1 / Item Type PSScene3Band doesn't exist"
    )

    oid = 'f8da0a3e-174f-4359-b088-a961ac76f0e7'
    id_not_found_msg = {
        "message": f"Could not load order ID: {oid}."
    }
    msg = http.BaseSession._parse_message(mock_response(
            HTTPStatus.NOT_FOUND,
            json=id_not_found_msg
        ))
    assert msg == f"Could not load order ID: {oid}."

    bad_oid = 'f8da0a3e-174f-4359-b088-a961ac76f0e'
    bad_id_msg = {
        "code": 601,
        "message": f"order_id in path must be of type uuid: \"{bad_oid}\""
    }
    msg = http.BaseSession._parse_message(mock_response(
            HTTPStatus.BAD_REQUEST,
            json=bad_id_msg
        ))
    assert msg == f'order_id in path must be of type uuid: "{bad_oid}"'


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
async def test_session_request_retry(mock_request, mock_response):
    async with http.Session() as ps:
        route = respx.get(TEST_URL)
        route.side_effect = [
            httpx.Response(HTTPStatus.TOO_MANY_REQUESTS, json={}),
            httpx.Response(HTTPStatus.OK, json={})
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
            await ps._retry(test_func)


@respx.mock
@pytest.mark.asyncio
async def test_authsession_request(mock_request):
    sess = http.AuthSession()
    mock_resp = httpx.Response(HTTPStatus.OK, text='bubba')
    respx.get(TEST_URL).return_value = mock_resp

    resp = sess.request(mock_request)
    assert resp.http_response.text == 'bubba'


def test_authsession__raise_for_status(mock_response):
    with pytest.raises(exceptions.APIException):
        http.AuthSession._raise_for_status(mock_response(
            HTTPStatus.BAD_REQUEST,
            json={}
            ))

    with pytest.raises(exceptions.APIException):
        http.AuthSession._raise_for_status(mock_response(
            HTTPStatus.UNAUTHORIZED,
            json={}
            ))
