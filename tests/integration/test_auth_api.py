# Copyright 2021 Planet Labs, Inc.
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
import logging

import httpx
import jwt
import pytest
import respx

from planet import exceptions
from planet.auth import AuthClient


TEST_URL = 'http://MockNotRealURL/'
AUTH_URL = TEST_URL + 'v0/auth/'

LOGGER = logging.getLogger(__name__)


@respx.mock
def test_AuthClient_success():
    login_url = AUTH_URL + 'login'

    payload = {'api_key': 'iamakey'}
    resp = {'token': jwt.encode(payload, 'key')}
    mock_resp = httpx.Response(HTTPStatus.OK, json=resp)
    respx.post(login_url).return_value = mock_resp

    cl = AuthClient(base_url=TEST_URL)
    auth_data = cl.login('email', 'password')

    assert auth_data == payload


@respx.mock
def test_AuthClient_invalid_email():
    login_url = AUTH_URL + 'login'

    resp = {
        "errors": {
            "email": [
                "Not a valid email address."
            ]
        },
        "message": "error validating request against UserAuthenticationSchema",
        "status": 400,
        "success": False
    }
    mock_resp = httpx.Response(400, json=resp)
    respx.post(login_url).return_value = mock_resp

    cl = AuthClient(base_url=TEST_URL)
    with pytest.raises(exceptions.APIException,
                       match='Not a valid email address.'):
        _ = cl.login('email', 'password')


@respx.mock
def test_AuthClient_invalid_password():
    login_url = AUTH_URL + 'login'

    resp = {
        "errors": None,
        "message": "Invalid email or password",
        "status": 401,
        "success": False
    }
    mock_resp = httpx.Response(401, json=resp)
    respx.post(login_url).return_value = mock_resp

    cl = AuthClient(base_url=TEST_URL)
    with pytest.raises(exceptions.APIException,
                       match='Incorrect email or password.'):
        _ = cl.login('email', 'password')
