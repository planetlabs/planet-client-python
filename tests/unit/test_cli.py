# # Copyright 2021 Planet Labs, Inc.
# #
# # Licensed under the Apache License, Version 2.0 (the "License"); you may not
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
from unittest.mock import MagicMock

from click.testing import CliRunner
import pytest

import planet
from planet.scripts.cli import cli

LOGGER = logging.getLogger(__name__)


TEST_OID = 'a8e74f65-5fbd-4b2c-917e-8b69b7e0772b'


@pytest.fixture(autouse=True)
def patch_session(monkeypatch):
    '''Make sure we don't actually make any http calls'''
    monkeypatch.setattr(planet, 'Session', MagicMock(spec=planet.Session))


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_auth_init_bad_pw(runner, monkeypatch):
    def apiexcept(*args, **kwargs):
        raise planet.api.exceptions.APIException('nope')
    monkeypatch.setattr(planet.Auth, 'from_login', apiexcept)
    result = runner.invoke(cli, args=['auth', 'init'], input='email\npw\n')
    assert 'Error: nope' in result.output


def test_cli_auth_init_success(runner, monkeypatch):
    mock_api_auth = MagicMock(spec=planet.auth.APIKeyAuth)
    mock_auth = MagicMock(spec=planet.Auth)
    mock_auth.from_login.return_value = mock_api_auth
    monkeypatch.setattr(planet, 'Auth', mock_auth)

    result = runner.invoke(cli, args=['auth', 'init'], input='email\npw\n')
    mock_auth.from_login.assert_called_once()
    mock_api_auth.write.assert_called_once()
    assert 'Initialized' in result.output


def test_cli_auth_value_failure(runner, monkeypatch):
    def authexception(*args, **kwargs):
        raise planet.auth.AuthException

    monkeypatch.setattr(planet.Auth, 'from_file', authexception)

    result = runner.invoke(cli, ['auth', 'value'])
    assert 'Error: Auth information does not exist or is corrupted.' \
        in result.output


def test_cli_auth_value_success(runner):
    result = runner.invoke(cli, ['auth', 'value'])
    assert not result.exception
    assert result.output == 'testkey\n'


def test_cli_orders_list_empty(runner, monkeypatch):
    async def lo(*arg, **kwarg):
        return []
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'list_orders', lo)

    result = runner.invoke(cli, ['orders', 'list'])
    assert not result.exception
    assert '[]' in result.output


def test_cli_orders_list_success(runner, monkeypatch):
    async def lo(*arg, **kwarg):
        return [{'order': 'yep'}]

    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'list_orders', lo)
    result = runner.invoke(cli, ['orders', 'list'])
    assert not result.exception
    assert "{'order': 'yep'}" in result.output


def test_cli_orders_get(runner, monkeypatch, order_description):
    async def go(*arg, **kwarg):
        return planet.api.orders.Order(order_description)

    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'get_order', go)
    result = runner.invoke(
        cli, ['orders', 'get', TEST_OID])
    assert not result.exception


def test_cli_orders_cancel(runner, monkeypatch, order_description):
    async def co(*arg, **kwarg):
        return ''

    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'cancel_order', co)
    result = runner.invoke(
        cli, ['orders', 'cancel', TEST_OID])
    assert not result.exception


def test_cli_orders_download(runner, monkeypatch):
    async def do(*arg, **kwarg):
        return ['file1']
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'download_order', do)

    async def poll(*arg, **kwarg):
        return
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'poll', poll)

    result = runner.invoke(
        cli, ['orders', 'download', TEST_OID])
    assert not result.exception
    # assert "file1" in result.output
    assert 'Downloaded 1 files.\n' == result.output
