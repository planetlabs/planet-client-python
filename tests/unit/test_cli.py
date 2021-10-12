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


def test_cli_info_verbosity(runner, monkeypatch):
    log_level = None

    def configtest(stream, level, format):
        nonlocal log_level
        log_level = level
    monkeypatch.setattr(planet.scripts.cli.logging, 'basicConfig', configtest)

    def patch(*args, **kwargs):
        pass
    monkeypatch.setattr(planet.scripts.cli, 'value', patch)

    _ = runner.invoke(cli, args=['auth', 'value'])
    assert log_level == logging.WARNING

    _ = runner.invoke(cli, args=['-v', 'auth', 'value'])
    assert log_level == logging.INFO

    _ = runner.invoke(cli, args=['-vv', 'auth', 'value'])
    assert log_level == logging.DEBUG


def test_cli_auth_init_bad_pw(runner, monkeypatch):
    def apiexcept(*args, **kwargs):
        raise planet.exceptions.APIException('nope')
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
    assert '{"order": "yep"}' in result.output


def test_cli_orders_get(runner, monkeypatch, order_description, oid):
    async def go(*arg, **kwarg):
        return planet.models.Order(order_description)

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
    all_test_files = ['file1.json', 'file2.zip', 'file3.tiff', 'file4.jpg']

    async def do(*arg, **kwarg):
        return all_test_files
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'download_order', do)

    async def poll(*arg, **kwarg):
        return
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'poll', poll)

    result = runner.invoke(
        cli, ['orders', 'download', oid])
    assert not result.exception

    # Check the output is as expected (list all files downloaded line-by-line)
    # Add a new line character (\n) for each test filename
    all_test_files_newline = '\n'.join(all_test_files) + '\n'
    # Expect output to look like 'file1\nfile2\n...fileN\n'
    assert all_test_files_newline == result.output


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
def mock_create_order(monkeypatch, order_description):
    mock_create_order = AsyncMock(
            return_value=planet.models.Order(order_description))
    monkeypatch.setattr(planet.scripts.cli.OrdersClient, 'create_order',
                        mock_create_order)
    return mock_create_order


@pytest.fixture
def test_id(order_request):
    return order_request['products'][0]['item_ids'][0]


def test_cli_read_file_geojson(clipaoi, geom_geojson):
    with open(clipaoi, 'r') as cfile:
        res = planet.scripts.cli.read_file_geojson({}, 'clip', cfile)
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
        cli, create_order_basic_cmds + ['--cloudconfig', cc_file]
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
        cli, create_order_basic_cmds + ['--clip', clipaoi]
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
        cli, create_order_basic_cmds + ['--tools', tools]
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
        cli, [
            'orders', 'create',
            '--name', order_request['name'],
            '--id', success_ids,
            '--bundle', product['product_bundle'],
            '--item-type', product['item_type']
        ])

    assert not success_mult_ids_result.exception

    # id string is wrong format
    failed_mult_ids_result = runner.invoke(
        cli, [
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
        cli, [
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
        cli, create_order_basic_cmds + ['--cloudconfig', cloudconfig]
    )
    assert wrong_format_result.exception
    assert "File does not contain valid json." \
        in wrong_format_result.output

    # cloudconfig file doesn't exist
    doesnotexistfile = tmp_path / 'doesnotexist.json'
    doesnotexit_result = runner.invoke(
        cli, create_order_basic_cmds + ['--cloudconfig', doesnotexistfile]
    )
    assert doesnotexit_result.exception
    assert "No such file or directory" in doesnotexit_result.output


def test_cli_orders_create_validate_tools(
        runner, mock_create_order, create_order_basic_cmds,
        tools, clipaoi,
        ):

    clip_and_tools_result = runner.invoke(
        cli, create_order_basic_cmds + ['--tools', tools, '--clip', clipaoi]
    )
    assert clip_and_tools_result.exception


def test_cli_orders_create_validate_clip(
        runner, mock_create_order, create_order_basic_cmds,
        point_geom_geojson, write_to_tmp_json_file
        ):
    clip_point = write_to_tmp_json_file(point_geom_geojson, 'point.json')

    clip_point_result = runner.invoke(
        cli, create_order_basic_cmds + ['--clip', clip_point]
    )
    assert clip_point_result.exception
    assert "Invalid geometry type: Point is not Polygon" in \
        clip_point_result.output
