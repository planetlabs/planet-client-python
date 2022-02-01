# Copyright 2022 Planet Labs, PBC.
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
from unittest.mock import MagicMock

from click.testing import CliRunner
import httpx
import jwt
import pytest
import respx

import planet
from planet.cli import cli

TEST_URL = 'http://MockNotRealURL/'


@pytest.fixture(autouse=True)
def patch_session(monkeypatch):
    '''Make sure we don't actually make any http calls'''
    monkeypatch.setattr(planet, 'Session', MagicMock(spec=planet.Session))


@respx.mock
@pytest.mark.asyncio
def test_cli_auth_init_base_url():
    '''Test base url option

    Uses the auth init path to ensure the base url is changed to the mocked
    url. So, ends up testing the auth init path somewhat as well
    '''
    login_url = TEST_URL + 'login'

    payload = {'api_key': 'iamakey'}
    resp = {'token': jwt.encode(payload, 'key')}
    mock_resp = httpx.Response(HTTPStatus.OK, json=resp)
    respx.post(login_url).return_value = mock_resp

    result = CliRunner().invoke(
        cli.main,
        args=['auth', '--base-url', TEST_URL, 'init'],
        input='email\npw\n')

    assert not result.exception
