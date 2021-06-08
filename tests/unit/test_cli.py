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
from unittest.mock import MagicMock, Mock

from click.testing import CliRunner
import pytest

import planet
from planet.scripts.cli import cli

LOGGER = logging.getLogger(__name__)


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


def test_cli_orders_get(runner, monkeypatch, order_description, oid):
    async def go(*arg, **kwarg):
        return planet.api.orders.Order(order_description)

    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'get_order', go)
    result = runner.invoke(
        cli, ['orders', 'get', oid])
    assert not result.exception


def test_cli_orders_cancel(runner, monkeypatch, order_description, oid):
    async def co(*arg, **kwarg):
        return ''

    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'cancel_order', co)
    result = runner.invoke(
        cli, ['orders', 'cancel', oid])
    assert not result.exception


def test_cli_orders_download(runner, monkeypatch, oid):
    async def do(*arg, **kwarg):
        return ['file1']
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'download_order', do)

    async def poll(*arg, **kwarg):
        return
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'poll', poll)

    result = runner.invoke(
        cli, ['orders', 'download', oid])
    assert not result.exception
    # assert "file1" in result.output
    assert 'Downloaded 1 files.\n' == result.output


class AsyncMock(Mock):
    '''Mock an async function'''
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def cloudconfig(write_to_tmp_json_file):
    as3_details = {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            },
        'archive_type': 'zip',
    }
    return write_to_tmp_json_file(as3_details)


@pytest.fixture
def clipaoi(feature_geojson, write_to_tmp_json_file):
    return write_to_tmp_json_file(feature_geojson)


@pytest.fixture
def mock_create_order(monkeypatch, oid):
    mock_create_order = AsyncMock(return_value=oid)
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'create_order',
                        mock_create_order)
    return mock_create_order


@pytest.fixture
def test_ids(oid):
    # uuid generated with https://www.uuidgenerator.net/
    test_id2 = '65f4aa35-b46b-48ba-b165-12b49986795c'
    return oid, test_id2


@pytest.fixture
def create_order_params(oid):
    return {
        'id': oid,
        'name': 'test',
        'bundle': 'analytic_udm2',
        'item_type': 'PSScene4Band'
    }


def test_cli_orders_create_cloudconfig(
        runner, mock_create_order, create_order_params, cloudconfig, oid
        ):

    basic_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type'],
            '--cloudconfig', cloudconfig
              ]
    )
    assert not basic_result.exception
    assert f'Created order {oid}' in basic_result.output

    mock_create_order.assert_called_once()

    expected_details = planet.OrderDetails(
        create_order_params['name'],
        [planet.Product([create_order_params['id']],
                        create_order_params['bundle'],
                        create_order_params['item_type'])],
        delivery=planet.Delivery.from_file(cloudconfig)
        )
    mock_create_order.assert_called_with(expected_details)


def test_cli_read_file_geojson(clipaoi):
    with open(clipaoi, 'r') as cfile:
        res = planet.scripts.cli.read_file_geojson({}, 'clip', cfile)
    assert type(res) == planet.Geometry


def test_cli_orders_create_clip(
        runner, mock_create_order, create_order_params, clipaoi, oid,
        geom_geojson):
    basic_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type'],
            '--clip', clipaoi
              ]
    )
    assert not basic_result.exception
    assert f'Created order {oid}' in basic_result.output

    mock_create_order.assert_called_once()

    expected_details = planet.OrderDetails(
        create_order_params['name'],
        [planet.Product([create_order_params['id']],
                        create_order_params['bundle'],
                        create_order_params['item_type'])],
        tools=[planet.Tool('clip', {'aoi': geom_geojson})]
        )
    mock_create_order.assert_called_with(expected_details)


def test_cli_orders_create_validate_id(runner, mock_create_order,
                                       create_order_params, oid):
    # uuid generated with https://www.uuidgenerator.net/
    test_id2 = '65f4aa35-b46b-48ba-b165-12b49986795c'
    success_ids = ','.join([oid, test_id2])
    fail_ids = '1.2,2'

    # id string is correct format
    success_mult_ids_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', success_ids,
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type']
              ])
    # assert not success_mult_ids_result.exception
    assert f'Created order {oid}' in success_mult_ids_result.output

    # id string is wrong format
    failed_mult_ids_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', fail_ids,
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type']
              ])
    assert failed_mult_ids_result.exception
    assert "Invalid value for '--id': '1.2' is not a valid UUID." \
        in failed_mult_ids_result.output


def test_cli_orders_create_validate_item_type(runner, mock_create_order,
                                              create_order_params):
    fail_item_type = 'PSScene3Band'

    # item type is not valid for bundle
    failed_item_type_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', fail_item_type
              ])
    assert failed_item_type_result.exception
    assert "Invalid value for '--item-type'" in failed_item_type_result.output


def test_cli_orders_create_validate_cloudconfig(runner, mock_create_order,
                                                create_order_params, tmp_path):
    # write invalid text to file
    cc = tmp_path / 'cc.json'
    with open(cc, 'w') as fp:
        fp.write('')

    # cloudconfig file is wrong format
    wrong_format_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type'],
            '--cloudconfig', cc
              ])
    assert wrong_format_result.exception
    assert "File does not contain valid json." \
        in wrong_format_result.output

    # cloudconfig file doesn't exist
    doesnotexistfile = tmp_path / 'doesnotexist.json'
    doesnotexit_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type'],
            '--cloudconfig', doesnotexistfile
              ])
    assert doesnotexit_result.exception
    assert "No such file or directory" in doesnotexit_result.output


def test_cli_orders_create_validate_tools(runner, mock_create_order,
                                          create_order_params, tmp_path):
    basic_result = runner.invoke(
        cli, [
            'orders', 'create',
            '--name', create_order_params['name'],
            '--id', create_order_params['id'],
            '--bundle', create_order_params['bundle'],
            '--item-type', create_order_params['item_type'],
            '--clip', 'something',
              ]
    )
    # assert not basic_result.exception
    # assert f'Created order {d}' in basic_result.output
    raise NotImplementedError
