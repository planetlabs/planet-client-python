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
from unittest.mock import MagicMock, Mock

from click.testing import CliRunner
import pytest

import planet
from planet.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_session(monkeypatch):
    '''Make sure we don't actually make any http calls'''
    monkeypatch.setattr(planet, 'Session', MagicMock(spec=planet.Session))


@pytest.fixture
def patch_ordersclient(monkeypatch):
    def patch(to_patch, patch_with):
        monkeypatch.setattr(cli.orders.OrdersClient, to_patch, patch_with)
    return patch


def test_cli_orders_list_empty(runner, patch_ordersclient):
    async def lo(*arg, **kwarg):
        return []
    patch_ordersclient('list_orders', lo)

    result = runner.invoke(cli.main, ['orders', 'list'])
    assert not result.exception
    assert '[]' in result.output


def test_cli_orders_list_success(runner, patch_ordersclient):
    async def lo(*arg, **kwarg):
        return [{'order': 'yep'}]
    patch_ordersclient('list_orders', lo)

    result = runner.invoke(cli.main, ['orders', 'list'])
    assert not result.exception
    assert '{"order": "yep"}' in result.output


def test_cli_orders_get(runner, patch_ordersclient, order_description, oid):
    async def go(*arg, **kwarg):
        return planet.models.Order(order_description)
    patch_ordersclient('get_order', go)

    result = runner.invoke(
        cli.main, ['orders', 'get', oid])
    assert not result.exception


def test_cli_orders_cancel(runner, patch_ordersclient, order_description, oid):
    async def co(*arg, **kwarg):
        return ''
    patch_ordersclient('cancel_order', co)

    result = runner.invoke(
        cli.main, ['orders', 'cancel', oid])
    assert not result.exception


def test_cli_orders_download(runner, patch_ordersclient, oid):
    all_test_files = ['file1.json', 'file2.zip', 'file3.tiff', 'file4.jpg']

    async def do(*arg, **kwarg):
        return all_test_files
    patch_ordersclient('download_order', do)

    async def poll(*arg, **kwarg):
        return
    patch_ordersclient('poll', poll)

    # Number of files in all_test_files
    expected = 'Downloaded 4 files.\n'

    # allow for some progress reporting
    result = runner.invoke(
        cli.main, ['orders', 'download', oid])
    assert not result.exception
    assert expected in result.output

    # test quiet option, should be no progress reporting
    result = runner.invoke(
        cli.main, ['orders', 'download', '-q', oid])
    assert not result.exception
    assert expected == result.output


class AsyncMock(Mock):
    '''Mock an async function'''
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def cloudconfig():
    return {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            },
        'archive_type': 'zip',
    }


@pytest.fixture
def clipaoi(feature_geojson, write_to_tmp_json_file):
    return write_to_tmp_json_file(feature_geojson, 'clip.json')


@pytest.fixture
def tools_json(geom_geojson):
    return [
            {
                'clip': {'aoi': geom_geojson}
            }, {
                'composite': {}
            }
    ]


@pytest.fixture
def tools(tools_json, write_to_tmp_json_file):
    return write_to_tmp_json_file(tools_json, 'tools.json')


@pytest.fixture
def mock_create_order(patch_ordersclient, order_description):
    mock_create_order = AsyncMock(
            return_value=planet.models.Order(order_description))
    patch_ordersclient('create_order', mock_create_order)
    return mock_create_order


@pytest.fixture
def test_id(order_request):
    return order_request['products'][0]['item_ids'][0]


def test_cli_read_file_geojson(clipaoi, geom_geojson):
    with open(clipaoi, 'r') as cfile:
        res = cli.orders.read_file_geojson({}, 'clip', cfile)
    assert res == geom_geojson


@pytest.fixture
def create_order_basic_cmds(order_request, test_id):
    product = order_request['products'][0]
    return [
            'orders', 'create',
            '--name', order_request['name'],
            '--id', test_id,
            '--bundle', product['product_bundle'],
            '--item-type', product['item_type']
        ]


@pytest.fixture
def name(order_request):
    return order_request['name']


@pytest.fixture
def products(order_request, test_id):
    product = order_request['products'][0]
    return [
        planet.order_request.product(
            [test_id],
            product['product_bundle'],
            product['item_type'])
    ]


def test_cli_orders_create_cloudconfig(
        runner, mock_create_order, create_order_basic_cmds, name, products,
        cloudconfig, write_to_tmp_json_file
        ):
    cc_file = write_to_tmp_json_file(cloudconfig, 'cloudconfig.json')
    basic_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--cloudconfig', cc_file]
    )
    assert not basic_result.exception

    mock_create_order.assert_called_once()

    expected_details = {
        'name': name,
        'products': products,
        'delivery': cloudconfig
    }
    mock_create_order.assert_called_with(expected_details)


def test_cli_orders_create_clip(
        runner, mock_create_order, create_order_basic_cmds, name, products,
        clipaoi, geom_geojson
        ):
    basic_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--clip', clipaoi]
    )
    assert not basic_result.exception

    mock_create_order.assert_called_once()

    expected_details = {
        'name': name,
        'products': products,
        'tools': [{'clip': {'aoi': geom_geojson}}]
    }
    mock_create_order.assert_called_with(expected_details)


def test_cli_orders_create_tools(
        runner, mock_create_order, create_order_basic_cmds, name, products,
        tools, tools_json):
    basic_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--tools', tools]
    )
    assert not basic_result.exception

    mock_create_order.assert_called_once()

    expected_details = {
        'name': name,
        'products': products,
        'tools': tools_json
    }
    mock_create_order.assert_called_with(expected_details)


def test_cli_orders_create_validate_id(
        runner, mock_create_order, order_request, test_id
        ):
    # uuid generated with https://www.uuidgenerator.net/
    test_id2 = '65f4aa35-b46b-48ba-b165-12b49986795c'
    success_ids = ','.join([test_id, test_id2])
    fail_ids = '1,,2'

    product = order_request['products'][0]

    # id string is correct format
    success_mult_ids_result = runner.invoke(
        cli.main, [
            'orders', 'create',
            '--name', order_request['name'],
            '--id', success_ids,
            '--bundle', product['product_bundle'],
            '--item-type', product['item_type']
        ])

    assert not success_mult_ids_result.exception

    # id string is wrong format
    failed_mult_ids_result = runner.invoke(
        cli.main, [
            'orders', 'create',
            '--name', order_request['name'],
            '--id', fail_ids,
            '--bundle', product['product_bundle'],
            '--item-type', product['item_type']
        ])
    assert failed_mult_ids_result.exception
    assert "id cannot be empty" in failed_mult_ids_result.output


def test_cli_orders_create_validate_item_type(
        runner, mock_create_order, order_request, test_id
        ):
    # item type is not valid for bundle
    failed_item_type_result = runner.invoke(
        cli.main, [
            'orders', 'create',
            '--name', order_request['name'],
            '--id', test_id,
            '--bundle', 'analytic_udm2',
            '--item-type', 'PSScene3Band'
            ])
    assert failed_item_type_result.exception
    assert "Invalid value: item_type" in failed_item_type_result.output


def test_cli_orders_create_validate_cloudconfig(
        runner, mock_create_order, create_order_basic_cmds,
        tmp_path,
        ):
    # write invalid text to file
    cloudconfig = tmp_path / 'cc.json'
    with open(cloudconfig, 'w') as fp:
        fp.write('')

    wrong_format_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--cloudconfig', cloudconfig]
    )
    assert wrong_format_result.exception
    assert "File does not contain valid json." \
        in wrong_format_result.output

    # cloudconfig file doesn't exist
    doesnotexistfile = tmp_path / 'doesnotexist.json'
    doesnotexit_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--cloudconfig', doesnotexistfile]
    )
    assert doesnotexit_result.exception
    assert "No such file or directory" in doesnotexit_result.output


def test_cli_orders_create_validate_tools(
        runner, mock_create_order, create_order_basic_cmds,
        tools, clipaoi,
        ):

    clip_and_tools_result = runner.invoke(
        cli.main,
        create_order_basic_cmds + ['--tools', tools, '--clip', clipaoi]
    )
    assert clip_and_tools_result.exception


def test_cli_orders_create_validate_clip(
        runner, mock_create_order, create_order_basic_cmds,
        point_geom_geojson, write_to_tmp_json_file
        ):
    clip_point = write_to_tmp_json_file(point_geom_geojson, 'point.json')

    clip_point_result = runner.invoke(
        cli.main, create_order_basic_cmds + ['--clip', clip_point]
    )
    assert clip_point_result.exception
    assert "Invalid geometry type: Point is not Polygon" in \
        clip_point_result.output
