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
"""Test Orders CLI"""
import copy
import hashlib
from http import HTTPStatus
import json
from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner
import httpx
import pytest
import respx

from planet.cli import cli

TEST_URL = 'http://MockNotRealURL/api/path'
TEST_DOWNLOAD_URL = f'{TEST_URL}/download'
TEST_ORDERS_URL = 'https://api.planet.com/compute/ops/orders/v2'

# NOTE: These tests use a lot of the same mocked responses as test_orders_api.


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = ['orders'] + extra_args
        return runner.invoke(cli.main, args=args)

    return _invoke


@pytest.fixture
def stac_json():
    return {'stac': {}}


@respx.mock
def test_cli_orders_list_basic(invoke, order_descriptions):
    next_page_url = TEST_ORDERS_URL + '/blob/?page_marker=IAmATest'
    order1, order2, order3 = order_descriptions
    page1_response = {
        "_links": {
            "_self": "string", "next": next_page_url
        },
        "orders": [order1, order2]
    }
    mock_resp1 = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp1

    page2_response = {"_links": {"_self": next_page_url}, "orders": [order3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    result = invoke(['list'])
    assert result.exit_code == 0
    sequence = '\n'.join([json.dumps(o) for o in [order1, order2, order3]])
    assert result.output == sequence + '\n'


@respx.mock
def test_cli_orders_list_empty(invoke):
    page1_response = {"_links": {"_self": "string"}, "orders": []}
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list'])
    assert result.exit_code == 0
    assert result.output == ''


@respx.mock
def test_cli_orders_list_filtering_and_sorting(invoke, order_descriptions):
    list_url = TEST_ORDERS_URL + '?source_type=all&state=failed&name=my_order_xyz&name__contains=xyz&created_on=2018-02-12T00:00:00Z/..&last_modified=../2018-03-18T12:31:12Z&hosting=true&sort_by=name DESC'

    order1, order2, _ = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string"
        }, "orders": [order1, order2]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(list_url).return_value = mock_resp

    # if the value of each arg doesn't get sent as a url parameter,
    # the mock will fail and this test will fail
    result = invoke([
        'list',
        '--state',
        'failed',
        '--name',
        'my_order_xyz',
        '--name-contains',
        'xyz',
        '--created-on',
        '2018-02-12T00:00:00Z/..',
        '--last-modified',
        '../2018-03-18T12:31:12Z',
        '--hosting',
        'true',
        '--sort-by',
        'name DESC'
    ])
    assert result.exit_code == 0
    sequence = '\n'.join([json.dumps(o) for o in [order1, order2]])
    assert result.output == sequence + '\n'


@respx.mock
@pytest.mark.parametrize("limit,limited_list_length", [(None, 100), (0, 102),
                                                       (1, 1)])
def test_cli_orders_list_limit(invoke,
                               order_descriptions,
                               limit,
                               limited_list_length):
    # Creating 102 (3x34) order descriptions
    long_order_descriptions = order_descriptions * 34

    all_orders = {}
    for x in range(1, len(long_order_descriptions) + 1):
        all_orders["order{0}".format(x)] = long_order_descriptions[x - 1]

    page1_response = {
        "_links": {
            "_self": "string"
        },
        "orders": [
            all_orders['order%s' % num]
            for num in range(1, limited_list_length + 1)
        ]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)

    # limiting is done within the client, no change to api call
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list', '--limit', limit])
    assert result.exit_code == 0
    count = len(result.output.strip().split('\n'))
    assert count == limited_list_length


@respx.mock
def test_cli_orders_list_pretty(invoke, monkeypatch, order_description):
    mock_echo_json = Mock()
    monkeypatch.setattr(cli.orders, 'echo_json', mock_echo_json)

    page1_response = {
        "_links": {
            "_self": "string"
        }, "orders": [order_description]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list', '--pretty'])
    assert result.exit_code == 0
    mock_echo_json.assert_called_once_with(order_description, True)


# TODO: add tests for "get --pretty" (gh-491).
@respx.mock
def test_cli_orders_get(invoke, oid, order_description):
    get_url = f'{TEST_ORDERS_URL}/{oid}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    result = invoke(['get', oid])
    assert result.exit_code == 0
    assert order_description == json.loads(result.output)


@respx.mock
def test_cli_orders_get_id_not_found(invoke, oid):
    get_url = f'{TEST_ORDERS_URL}/{oid}'
    error_json = {"message": "Error message"}
    mock_resp = httpx.Response(404, json=error_json)
    respx.get(get_url).return_value = mock_resp

    result = invoke(['get', oid])
    assert result.exit_code == 1
    assert 'Error: {"message": "Error message"}\n' == result.output


# TODO: add tests for "cancel --pretty" (gh-491).
@respx.mock
def test_cli_orders_cancel(invoke, oid, order_description):
    cancel_url = f'{TEST_ORDERS_URL}/{oid}'
    order_description['state'] = 'cancelled'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.put(cancel_url).return_value = mock_resp

    result = invoke(['cancel', oid])
    assert result.exit_code == 0
    assert str(mock_resp.json()) + '\n' == result.output


@respx.mock
def test_cli_orders_cancel_id_not_found(invoke, oid):
    cancel_url = f'{TEST_ORDERS_URL}/{oid}'
    error_json = {"message": "Error message"}
    mock_resp = httpx.Response(404, json=error_json)
    respx.put(cancel_url).return_value = mock_resp

    result = invoke(['cancel', oid])
    assert result.exit_code == 1
    assert 'Error: {"message": "Error message"}\n' == result.output


# TODO: add tests for "wait --state" (gh-492) and "wait --pretty" (gh-491).
@respx.mock
def test_cli_orders_wait_default(invoke, order_description, oid):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2)
    ]

    runner = CliRunner()
    result = invoke(['wait', '--delay', '0', oid], runner=runner)
    assert result.exit_code == 0
    assert result.output.endswith('success\n')


@respx.mock
def test_cli_orders_wait_max_attempts(invoke, order_description, oid):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'running'
    order_description3 = copy.deepcopy(order_description)
    order_description3['state'] = 'success'

    route = respx.get(get_url)
    route.side_effect = [httpx.Response(HTTPStatus.OK, json=order_description)]

    runner = CliRunner()
    result = invoke(['wait', '--delay', '0', '--max-attempts', '1', oid],
                    runner=runner)
    assert result.exit_code == 1
    assert result.output.endswith(
        'Error: Maximum number of attempts (1) reached.\n')


@pytest.fixture
def mock_download_response(oid, order_description):

    def _func():
        # Mock an HTTP response for download
        order_description['state'] = 'success'
        dl_url1 = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'
        dl_url2 = TEST_DOWNLOAD_URL + '/2?token=IAmAnotherToken'
        dl_url3 = TEST_DOWNLOAD_URL + '/manifest'

        order_description['_links']['results'] = [{
            'location': dl_url1,
            'name': f'{oid}/itemtype/m1.json'
        }, {
            'location': dl_url2,
            'name': f'{oid}/itemtype/m2.json'
        }, {
            'location': dl_url3,
            'name': f'{oid}/manifest.json'
        }]  # yapf: disable

        get_url = f'{TEST_ORDERS_URL}/{oid}'
        mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
        respx.get(get_url).return_value = mock_resp

        mock_resp1 = httpx.Response(HTTPStatus.OK,
                                    json={'key': 'value'},
                                    headers={
                                        'Content-Type':
                                        'application/json',
                                        'Content-Disposition':
                                        'attachment; filename="m1.json"'
                                    })
        respx.get(dl_url1).return_value = mock_resp1

        mock_resp2 = httpx.Response(HTTPStatus.OK,
                                    json={'key2': 'value2'},
                                    headers={
                                        'Content-Type':
                                        'application/json',
                                        'Content-Disposition':
                                        'attachment; filename="m2.json"'
                                    })
        respx.get(dl_url2).return_value = mock_resp2

        m1_bytes = b'{"key": "value"}'
        m2_bytes = b'{"key2": "value2"}'
        manifest_data = {
            "name": "",
            "files": [
                {
                    "path": "itemtype/m1.json",
                    "digests": {
                        "md5": hashlib.md5(m1_bytes).hexdigest(),
                        "sha256": hashlib.sha256(m1_bytes).hexdigest()}
                }, {
                    "path": "itemtype/m2.json",
                    "digests": {
                        "md5": hashlib.md5(m2_bytes).hexdigest(),
                        "sha256": hashlib.sha256(m2_bytes).hexdigest()}
                }]
        }  # yapf: disable
        mock_resp3 = httpx.Response(HTTPStatus.OK,
                                    json=manifest_data,
                                    headers={
                                        'Content-Type':
                                        'application/json',
                                        'Content-Disposition':
                                        'attachment; filename="manifest.json"'
                                    })
        respx.get(dl_url3).return_value = mock_resp3

    return _func


@respx.mock
def test_cli_orders_download_default(invoke, mock_download_response, oid):
    mock_download_response()

    runner = CliRunner()
    with runner.isolated_filesystem() as folder:
        result = invoke(['download', oid], runner=runner)
        assert result.exit_code == 0

        # basic check of progress reporting
        assert 'm1.json' in result.output

        # Check that the files were downloaded and have the correct contents
        with open(Path(folder) / f'{oid}/itemtype/m1.json') as f:
            assert json.load(f) == {'key': 'value'}
        with open(Path(folder) / f'{oid}/itemtype/m2.json') as f:
            assert json.load(f) == {'key2': 'value2'}


@respx.mock
def test_cli_orders_download_checksum(invoke, mock_download_response, oid):
    """checksum is successful"""
    mock_download_response()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = invoke(['download', oid, '--checksum=MD5'], runner=runner)
        assert result.exit_code == 0


@respx.mock
def test_cli_orders_download_dest(invoke, mock_download_response, oid):
    mock_download_response()

    runner = CliRunner()
    with runner.isolated_filesystem() as folder:
        dest_dir = Path(folder) / 'foobar'
        dest_dir.mkdir()
        result = invoke(['download', '--directory', 'foobar', oid],
                        runner=runner)
        assert result.exit_code == 0

        # Check that the files were downloaded to the custom directory
        with open(dest_dir / f'{oid}/itemtype/m1.json') as f:
            assert json.load(f) == {'key': 'value'}

        with open(dest_dir / f'{oid}/itemtype/m2.json') as f:
            assert json.load(f) == {'key2': 'value2'}


@respx.mock
def test_cli_orders_download_overwrite(invoke,
                                       mock_download_response,
                                       oid,
                                       write_to_tmp_json_file):
    mock_download_response()

    runner = CliRunner()
    with runner.isolated_filesystem() as folder:
        filepath = Path(folder) / f'{oid}/itemtype/m1.json'
        filepath.parent.mkdir(parents=True)
        filepath.write_text(json.dumps({'foo': 'bar'}))

        # check the file doesn't get overwritten by default
        result = invoke(['download', oid], runner=runner)
        assert result.exit_code == 0

        with open(filepath, 'r') as f:
            assert json.load(f) == {'foo': 'bar'}

        # check the file gets overwritten
        result = invoke(['download', '--overwrite', oid], runner=runner)
        assert result.exit_code == 0

        with open(filepath, 'r') as f:
            assert json.load(f) == {'key': 'value'}


@respx.mock
def test_cli_orders_download_state(invoke, order_description, oid):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description['state'] = 'running'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    runner = CliRunner()
    result = invoke(['download', oid], runner=runner)

    assert result.exit_code == 1
    assert 'order state (running) is not a final state.' in result.output


@respx.mock
def test_cli_orders_create_basic_success(invoke, order_description):
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ['4500474_2133707_2021-05-20_2419'],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic"
        }],
    }

    result = CliRunner().invoke(
        cli.main, ['orders', 'create', json.dumps(order_request)],
        catch_exceptions=True)

    assert result.exit_code == 0
    assert json.loads(
        result.output)['_links']['results'][0]['delivery'] == 'success'


@pytest.mark.parametrize(
    "id_string, expected_ids",
    [('4500474_2133707_2021-05-20_2419', ['4500474_2133707_2021-05-20_2419']),
     ('4500474_2133707_2021-05-20_2419,4500474_2133707_2021-05-20_2420',
      ['4500474_2133707_2021-05-20_2419', '4500474_2133707_2021-05-20_2420'])])
def test_cli_orders_request_basic_success(expected_ids,
                                          id_string,
                                          invoke,
                                          stac_json):
    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        id_string,
    ])
    assert not result.exception

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": expected_ids,
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic"
        }],
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


def test_cli_orders_request_item_type_invalid(invoke):
    result = invoke([
        'request',
        '--item-type=invalid'
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
    ])
    assert result.exit_code == 2


def test_cli_orders_request_product_bundle_invalid(invoke):
    result = invoke([
        'request',
        '--item-type=PSScene'
        '--bundle=invalid',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
    ])
    assert result.exit_code == 2


def test_cli_orders_request_product_bundle_incompatible(invoke):
    result = invoke([
        'request',
        '--item-type=PSScene',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
    ])
    assert result.exit_code == 2


def test_cli_orders_request_id_empty(invoke):
    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        ''
    ])
    assert result.exit_code == 2
    assert 'Entry cannot be an empty string.' in result.output


@pytest.mark.parametrize("geom_fixture",
                         [('geom_geojson'), ('feature_geojson'),
                          ('featurecollection_geojson')])
def test_cli_orders_request_clip_polygon(geom_fixture,
                                         request,
                                         invoke,
                                         geom_geojson,
                                         stac_json):

    geom = request.getfixturevalue(geom_fixture)

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--clip={json.dumps(geom)}',
    ])
    assert result.exit_code == 0

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "tools": [{
            'clip': {
                'aoi': geom_geojson
            }
        }],
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


@pytest.mark.parametrize("geom_fixture", [('geom_reference')])
def test_cli_orders_request_clip_ref(geom_fixture, request, invoke, stac_json):

    geom = request.getfixturevalue(geom_fixture)

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--clip={json.dumps(geom)}',
    ])
    assert result.exit_code == 0

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "tools": [{
            'clip': {
                'aoi': geom
            }
        }],
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


def test_cli_orders_request_clip_multipolygon(multipolygon_geom_geojson,
                                              invoke,
                                              geom_geojson,
                                              stac_json):

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--clip={json.dumps(multipolygon_geom_geojson)}',
    ])
    assert result.exit_code == 0

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "tools": [{
            'clip': {
                'aoi': multipolygon_geom_geojson
            }
        }],
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


def test_cli_orders_request_clip_invalid_geometry(invoke, point_geom_geojson):
    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--clip={json.dumps(point_geom_geojson)}'
    ])
    assert result.exit_code == 2


def test_cli_orders_request_both_clip_and_tools(invoke, geom_geojson):
    # interestingly, it is important that both clip and tools
    # option values are valid json
    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--clip={json.dumps(geom_geojson)}',
        f'--tools={json.dumps(geom_geojson)}'
    ])

    assert result.exit_code == 2
    assert "Specify only one of '--clip' or '--tools'" in result.output


def test_cli_orders_request_cloudconfig(invoke, stac_json):
    config_json = {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
        },
        'archive_type': 'zip'
    }

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--cloudconfig={json.dumps(config_json)}',
    ])
    assert result.exit_code == 0

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "delivery":
        config_json,
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


def test_cli_orders_request_email(invoke, stac_json):
    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        '--email'
    ])
    assert result.exit_code == 0

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "notifications": {
            "email": True,
        },
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


@respx.mock
def test_cli_orders_request_tools(invoke, geom_geojson, stac_json):
    tools_json = [{'clip': {'aoi': geom_geojson}}, {'composite': {}}]

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        f'--tools={json.dumps(tools_json)}'
    ])

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }],
        "tools":
        tools_json,
        "metadata":
        stac_json
    }
    assert order_request == json.loads(result.output)


@respx.mock
def test_cli_orders_request_no_stac(invoke):

    result = invoke([
        'request',
        '--item-type=PSOrthoTile',
        '--bundle=analytic',
        '--name=test',
        '4500474_2133707_2021-05-20_2419',
        '--no-stac'
    ])

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["4500474_2133707_2021-05-20_2419"],
            "item_type": "PSOrthoTile",
            "product_bundle": "analytic",
        }]
    }
    assert order_request == json.loads(result.output)


@respx.mock
def test_cli_orders_request_hosting_sentinel_hub(invoke, stac_json):

    result = invoke([
        'request',
        '--item-type=PSScene',
        '--bundle=visual',
        '--name=test',
        '20220325_131639_20_2402',
        '--hosting=sentinel_hub',
    ])

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["20220325_131639_20_2402"],
            "item_type": "PSScene",
            "product_bundle": "visual",
        }],
        "metadata":
        stac_json,
        "hosting": {
            "sentinel_hub": {}
        }
    }
    assert order_request == json.loads(result.output)


@respx.mock
def test_cli_orders_request_hosting_sentinel_hub_collection_id(
        invoke, stac_json):

    result = invoke([
        'request',
        '--item-type=PSScene',
        '--bundle=visual',
        '--name=test',
        '20220325_131639_20_2402',
        '--hosting=sentinel_hub',
        '--collection_id=1234'
    ])

    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ["20220325_131639_20_2402"],
            "item_type": "PSScene",
            "product_bundle": "visual",
        }],
        "metadata":
        stac_json,
        "hosting": {
            "sentinel_hub": {
                "collection_id": "1234"
            }
        }
    }
    assert order_request == json.loads(result.output)
