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
"""Tests of the Data CLI."""
from http import HTTPStatus
import json
import logging
from pathlib import Path
import math

import httpx
import respx

from click.testing import CliRunner
import pytest

from planet.cli import cli
from planet.specs import get_item_types

LOGGER = logging.getLogger(__name__)

TEST_URL = 'https://api.planet.com/data/v1'
TEST_QUICKSEARCH_URL = f'{TEST_URL}/quick-search'
TEST_SEARCHES_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = ['data'] + extra_args
        return runner.invoke(cli.main, args=args)

    return _invoke


@pytest.fixture
def item_type():
    return 'PSScene'


@pytest.fixture
def item_id():
    return '20221003_002705_38_2461xx'


@pytest.fixture
def asset_type_id():
    return 'basic_udm2'


@pytest.fixture
def dl_url():
    return f'{TEST_URL}/1?token=IAmAToken'


@pytest.fixture
def mock_asset_get_response(item_type, item_id, asset_type_id, dl_url):

    def _func():
        basic_udm2_asset = {
            "_links": {
                "_self": "SELFURL",
                "activate": "ACTIVATEURL",
                "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": 'active',
            "location": dl_url,
            "type": asset_type_id
        }

        page_response = {
            "basic_analytic_4b": {
                "_links": {
                    "_self":
                    "SELFURL",
                    "activate":
                    "ACTIVATEURL",
                    "type":
                    "https://api.planet.com/data/v1/asset-types/basic_analytic_4b"
                },
                "_permissions": ["download"],
                "md5_digest": None,
                "status": "inactive",
                "type": "basic_analytic_4b"
            },
            "basic_udm2": basic_udm2_asset
        }

        # Mock the response for get_asset
        mock_resp_get = httpx.Response(HTTPStatus.OK, json=page_response)
        asset_url = f'{TEST_URL}/item-types/{item_type}/items/{item_id}/assets'
        respx.get(asset_url).return_value = mock_resp_get

    return _func


def test_data_command_registered(invoke):
    """planet-data command prints help and usage message."""
    runner = CliRunner()
    result = invoke(["--help"], runner=runner)
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "search" in result.output
    assert "search-create" in result.output
    assert "search-get" in result.output
    assert "search-delete" in result.output
    assert "search-update" in result.output
    assert "asset-download" in result.output
    assert "asset-activate" in result.output
    assert "asset-wait" in result.output
    # Add other sub-commands here.


def test_data_search_command_registered(invoke):
    """planet-data search command prints help and usage message."""
    runner = CliRunner()
    result = invoke(["search", "--help"], runner=runner)
    all_item_types = [a for a in get_item_types()]
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "limit" in result.output
    assert "name" in result.output
    assert "sort" in result.output
    assert "pretty" in result.output
    assert "help" in result.output
    for a in all_item_types:
        assert a in result.output.replace('\n', '').replace(' ', '')
    # Add other sub-commands here.


PERMISSION_FILTER = {"type": "PermissionFilter", "config": ["assets:download"]}
STD_QUALITY_FILTER = {
    "type": "StringInFilter",
    "field_name": "quality_category",
    "config": ["standard"]
}


@pytest.fixture()
def default_filters():
    return [PERMISSION_FILTER, STD_QUALITY_FILTER]


@pytest.fixture
def search_filter(get_test_file_json):
    filename = 'data_search_filter_2022-01.json'
    return get_test_file_json(filename)


@pytest.fixture
def assert_and_filters_equal():
    """Check for equality when the order of the config list doesn't matter"""

    def _func(filter1, filter2):
        assert filter1.keys() == filter2.keys()
        assert filter1['type'] == filter2['type']

        assert len(filter1['config']) == len(filter2['config'])
        for c in filter1['config']:
            assert c in filter2['config']

    return _func


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("permission, p_remove",
                         [(None, None),
                          ('--permission=False', PERMISSION_FILTER)])
@pytest.mark.parametrize("std_quality, s_remove",
                         [(None, None),
                          ('--std-quality=False', STD_QUALITY_FILTER)])
def test_data_filter_defaults(permission,
                              p_remove,
                              std_quality,
                              s_remove,
                              invoke,
                              default_filters,
                              assert_and_filters_equal):
    runner = CliRunner()

    args = [arg for arg in [permission, std_quality] if arg]
    result = invoke(["filter", *args], runner=runner)
    assert result.exit_code == 0

    [default_filters.remove(rem) for rem in [p_remove, s_remove] if rem]
    expected_filt = {"type": "AndFilter", "config": default_filters}
    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("asset, expected",
                         [('ortho_analytic_8b_sr', ['ortho_analytic_8b_sr']),
                          ('ortho_analytic_8b_sr,ortho_analytic_4b_sr',
                           ['ortho_analytic_8b_sr', 'ortho_analytic_4b_sr']),
                          ('ortho_analytic_8b_sr , ortho_analytic_4b_sr',
                           ['ortho_analytic_8b_sr', 'ortho_analytic_4b_sr'])])
def test_data_filter_asset(asset,
                           expected,
                           invoke,
                           default_filters,
                           assert_and_filters_equal):
    runner = CliRunner()

    result = invoke(["filter", f'--asset={asset}'], runner=runner)
    assert result.exit_code == 0

    asset_filter = {"type": "AssetFilter", "config": expected}
    expected_filt = {
        "type": "AndFilter", "config": default_filters + [asset_filter]
    }
    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_date_range_success(invoke,
                                        assert_and_filters_equal,
                                        default_filters):
    """Check filter is created correctly and that multiple options results in
    multiple filters"""
    runner = CliRunner()

    result = invoke(["filter"] + '--date-range field gt 2021-01-01'.split() +
                    '--date-range field2 lt 2022-01-01'.split(),
                    runner=runner)
    assert result.exit_code == 0

    date_range_filter1 = {
        "type": "DateRangeFilter",
        "field_name": "field",
        "config": {
            "gt": "2021-01-01T00:00:00Z"
        }
    }
    date_range_filter2 = {
        "type": "DateRangeFilter",
        "field_name": "field2",
        "config": {
            "lt": "2022-01-01T00:00:00Z"
        }
    }

    expected_filt = {
        "type": "AndFilter",
        "config": default_filters + [date_range_filter1, date_range_filter2]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_date_range_invalid(invoke):
    runner = CliRunner()

    result = invoke(["filter"] + '--date-range field gt 2021'.split(),
                    runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("geom_fixture",
                         [('geom_geojson'), ('feature_geojson'),
                          ('featurecollection_geojson')])
def test_data_filter_geom(geom_fixture,
                          request,
                          invoke,
                          geom_geojson,
                          assert_and_filters_equal,
                          default_filters):
    """Ensure that all GeoJSON forms of describing a geometry are handled
    and all result in the same, valid GeometryFilter being created"""
    runner = CliRunner()

    geom = request.getfixturevalue(geom_fixture)
    geom_str = json.dumps(geom)
    result = invoke(["filter", f'--geom={geom_str}'], runner=runner)
    assert result.exit_code == 0

    geom_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": geom_geojson
    }

    expected_filt = {
        "type": "AndFilter", "config": default_filters + [geom_filter]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_number_in_success(invoke,
                                       assert_and_filters_equal,
                                       default_filters):
    runner = CliRunner()

    result = invoke(["filter"] + '--number-in field 1'.split() +
                    '--number-in field2 2,3.5'.split(),
                    runner=runner)
    assert result.exit_code == 0

    number_in_filter1 = {
        "type": "NumberInFilter", "field_name": "field", "config": [1.0]
    }
    number_in_filter2 = {
        "type": "NumberInFilter", "field_name": "field2", "config": [2.0, 3.5]
    }

    expected_filt = {
        "type": "AndFilter",
        "config": default_filters + [number_in_filter1, number_in_filter2]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_number_in_badparam(invoke,
                                        assert_and_filters_equal,
                                        default_filters):
    runner = CliRunner()

    result = invoke(["filter"] + '--number-in field 1,str'.split(),
                    runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.asyncio
def test_data_filter_range(invoke, assert_and_filters_equal, default_filters):
    """Check filter is created correctly, that multiple options results in
    multiple filters, and that floats are processed correctly."""
    runner = CliRunner()

    result = invoke(["filter"] + '--range field gt 70'.split() +
                    '--range cloud_cover lt 0.5'.split(),
                    runner=runner)
    assert result.exit_code == 0

    range_filter1 = {
        "type": "RangeFilter", "field_name": "field", "config": {
            "gt": 70.0
        }
    }
    range_filter2 = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
            "lt": 0.5
        }
    }

    expected_filt = {
        "type": "AndFilter",
        "config": default_filters + [range_filter1, range_filter2]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_string_in(invoke,
                               assert_and_filters_equal,
                               default_filters):
    runner = CliRunner()

    result = invoke(["filter"] + '--string-in field foo'.split() +
                    '--string-in field2 foo,bar'.split(),
                    runner=runner)
    assert result.exit_code == 0

    string_in_filter1 = {
        "type": "StringInFilter", "field_name": "field", "config": ["foo"]
    }
    string_in_filter2 = {
        "type": "StringInFilter",
        "field_name": "field2",
        "config": ["foo", "bar"]
    }

    expected_filt = {
        "type": "AndFilter",
        "config": default_filters + [string_in_filter1, string_in_filter2]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
def test_data_filter_update(invoke, assert_and_filters_equal, default_filters):
    """Check filter is created correctly and that multiple options results in
    multiple filters"""
    runner = CliRunner()

    result = invoke(["filter"] + '--update field gt 2021-01-01'.split() +
                    '--update field2 gte 2022-01-01'.split(),
                    runner=runner)
    assert result.exit_code == 0

    update_filter1 = {
        "type": "UpdateFilter",
        "field_name": "field",
        "config": {
            "gt": "2021-01-01T00:00:00Z"
        }
    }
    update_filter2 = {
        "type": "UpdateFilter",
        "field_name": "field2",
        "config": {
            "gte": "2022-01-01T00:00:00Z"
        }
    }

    expected_filt = {
        "type": "AndFilter",
        "config": default_filters + [update_filter1, update_filter2]
    }

    assert_and_filters_equal(json.loads(result.output), expected_filt)


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", ['{1:1}', '{"foo"}'])
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
def test_data_search_cmd_filter_invalid_json(invoke, item_types, filter):
    """Test for planet data search_quick. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_QUICKSEARCH_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["search", item_types, filter], runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
def test_data_search_cmd_filter_success(invoke, item_types):
    """Test for planet data search_quick. Test with multiple item_types.
    Test should succeed as filter contains valid JSON."""
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }

    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_QUICKSEARCH_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["search", item_types, json.dumps(filter)], runner=runner)

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) == 1  # we have 1 feature


@respx.mock
def test_data_search_cmd_sort_success(invoke):
    # this cannot be the default value or else the sort param will not be
    # added to the url
    sort = 'published asc'
    search_url = f'{TEST_QUICKSEARCH_URL}?_sort={sort}'

    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z"
        }
    }

    feature = {"key": "value"}
    mock_resp = httpx.Response(HTTPStatus.OK, json={'features': [feature]})
    respx.post(search_url).return_value = mock_resp

    runner = CliRunner()
    result = invoke(
        ['search', 'PSScene', json.dumps(filter), f'--sort={sort}'],
        runner=runner)
    assert result.exit_code == 0
    assert json.loads(result.output) == feature


@respx.mock
def test_data_search_cmd_sort_invalid(invoke):
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z"
        }
    }

    runner = CliRunner()
    result = invoke(
        ['search', 'PSScene', json.dumps(filter), '--sort=invalid'],
        runner=runner)

    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize("limit,limited_list_length", [(None, 100), (0, 102),
                                                       (1, 1)])
def test_data_search_cmd_limit(invoke,
                               search_results,
                               limit,
                               limited_list_length):
    """Test for planet data search_quick limit option.

    If no value is specified, make sure the result contains at most 100
    entries.
    """
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }
    item_types = 'SkySatCollect'

    # Creating 102 (3x34) search results
    long_search_results = search_results * 34

    all_results = {}
    for x in range(1, len(long_search_results) + 1):
        all_results["result{0}".format(x)] = long_search_results[x - 1]

    page1_response = {
        "_links": {
            "_self": "string1", "assets": "string2", "thumbnail": "string3"
        },
        "features": [
            all_results[f'result{num}']
            for num in range(1, limited_list_length + 1)
        ]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)

    respx.post(TEST_QUICKSEARCH_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(
        ["search", item_types, json.dumps(filter), "--limit", limit],
        runner=runner)
    assert result.exit_code == 0
    assert result.output.count('"id"') == limited_list_length


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", ['{1:1}', '{"foo"}'])
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
def test_data_search_create_filter_invalid_json(invoke, item_types, filter):
    """Test for planet data search_create. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_SEARCHES_URL).return_value = mock_resp

    name = "temp"

    runner = CliRunner()
    result = invoke(["search-create", name, item_types, filter], runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
def test_data_search_create_filter_success(invoke, item_types):
    """Test for planet data search_create. Test with multiple item_types.
    Test should succeed as filter contains valid JSON."""
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }

    name = "temp"

    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_SEARCHES_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["search-create", name, item_types, json.dumps(filter)],
                    runner=runner)

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) == 1  # we have 1 feature


@respx.mock
def test_search_create_daily_email(invoke, search_result):
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_result)
    respx.post(TEST_SEARCHES_URL).return_value = mock_resp

    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }

    result = invoke([
        'search-create',
        'temp',
        'SkySatScene',
        json.dumps(filter),
        '--daily-email'
    ])

    search_request = {
        "name": "temp",
        "filter": {
            "type": "DateRangeFilter",
            "field_name": "acquired",
            "config": {
                "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
            }
        },
        "item_types": ["SkySatScene"],
        "__daily_email_enabled": True
    }
    sent_request = json.loads(respx.calls.last.request.content)
    assert result.exit_code == 0
    assert sent_request == search_request
    assert json.loads(result.output) == search_result


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", ['{1:1}', '{"foo"}'])
def test_data_stats_invalid_filter(invoke, filter):
    """Test for planet data stats. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_STATS_URL).return_value = mock_resp
    interval = "hour"
    item_type = 'PSScene'
    runner = CliRunner()
    result = invoke(["stats", item_type, interval, filter], runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
@pytest.mark.parametrize("interval, exit_code", [(None, 1), ('hou', 2),
                                                 ('hour', 0)])
def test_data_stats_invalid_interval(invoke, item_types, interval, exit_code):
    """Test for planet data stats. Test with multiple item_types.
    Test should succeed with valid interval, and fail with invalid interval."""
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }

    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_STATS_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["stats", item_types, interval, json.dumps(filter)],
                    runner=runner)

    assert result.exit_code == exit_code


@respx.mock
@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
@pytest.mark.parametrize("interval", ['hour', 'day', 'week', 'month', 'year'])
def test_data_stats_success(invoke, item_types, interval):
    """Test for planet data stats. Test with multiple item_types.

    Test should succeed as filter contains valid JSON, item_types, and
    intervals.
    """
    filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gt": "2019-12-31T00:00:00Z", "lte": "2020-01-31T00:00:00Z"
        }
    }

    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_STATS_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["stats", item_types, interval, json.dumps(filter)],
                    runner=runner)
    assert result.exit_code == 0


# TODO: basic test for "planet data filter".


@respx.mock
def test_search_get(invoke, search_id, search_result):
    get_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_result)
    respx.get(get_url).return_value = mock_resp

    result = invoke(['search-get', search_id])
    assert not result.exception
    assert search_result == json.loads(result.output)


@respx.mock
def test_search_get_id_not_found(invoke, search_id):
    get_url = f'{TEST_SEARCHES_URL}/{search_id}'
    error_json = {"message": "Error message"}
    mock_resp = httpx.Response(404, json=error_json)
    respx.get(get_url).return_value = mock_resp

    result = invoke(['search-get', search_id])
    assert result.exception
    assert 'Error: {"message": "Error message"}\n' == result.output


@respx.mock
def test_search_delete_success(invoke, search_id, search_result):
    delete_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(HTTPStatus.NO_CONTENT, json=search_result)
    respx.delete(delete_url).return_value = mock_resp

    result = invoke(['search-delete', search_id])

    assert not result.exception


@respx.mock
def test_search_delete_nonexistant_search_id(invoke, search_id, search_result):
    delete_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(404, json=search_result)
    respx.delete(delete_url).return_value = mock_resp

    result = invoke(['search-delete', search_id])

    assert result.exception
    assert result.exit_code == 1


@pytest.mark.parametrize("item_types",
                         ['PSScene', 'SkySatScene', 'PSScene, SkySatScene'])
@respx.mock
def test_search_update_success(invoke,
                               search_id,
                               search_result,
                               item_types,
                               search_filter):
    update_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_result)
    respx.put(update_url).return_value = mock_resp

    name = "search_name"

    result = invoke([
        'search-update',
        search_id,
        name,
        item_types,
        json.dumps(search_filter)
    ])

    assert not result.exception


@respx.mock
def test_search_update_fail(invoke, search_id, search_filter):
    update_url = f'{TEST_SEARCHES_URL}/{search_id}'
    error_json = {"message": "Error message"}
    mock_resp = httpx.Response(404, json=error_json)
    respx.put(update_url).return_value = mock_resp

    name = "search_name"
    item_types = "PSScene"

    result = invoke([
        'search-update',
        search_id,
        name,
        item_types,
        json.dumps(search_filter)
    ])

    assert result.output.startswith("Error")
    assert result.exception


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("exists, overwrite",
                         [(False, False), (True, False), (True, True),
                          (False, True)])
def test_asset_download_default(invoke,
                                open_test_img,
                                exists,
                                overwrite,
                                mock_asset_get_response,
                                item_type,
                                item_id,
                                asset_type_id,
                                dl_url):

    mock_asset_get_response()

    img_headers = {
        'Content-Type': 'image/tiff',
        'Content-Length': '527',
        'Content-Disposition': 'attachment; filename="img.tif"'
    }

    async def _stream_img():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v) / (chunksize))):
            yield v[i * chunksize:min((i + 1) * chunksize, len(v))]

    # Mock the response for download_asset
    mock_resp_download = httpx.Response(HTTPStatus.OK,
                                        stream=_stream_img(),
                                        headers=img_headers,
                                        request='donotcloneme')
    respx.get(dl_url).return_value = mock_resp_download

    runner = CliRunner()
    with runner.isolated_filesystem() as folder:
        if exists:
            Path(folder, 'img.tif').write_bytes(b'01010')

        asset_download_command = [
            'asset-download',
            item_type,
            item_id,
            asset_type_id,
            f'--directory={Path(folder)}',
            '--filename',
            'img.tif'
        ]
        if overwrite:
            asset_download_command.append('--overwrite')

        result = invoke(asset_download_command, runner=runner)
        assert result.exit_code == 0

        path = Path(folder, 'img.tif')

        assert path.name == 'img.tif'
        assert path.is_file()

        if exists and not overwrite:
            assert len(path.read_bytes()) == 5
            assert len(result.output) == 0
        else:
            assert len(path.read_bytes()) == 527
            assert path.name in result.output


@respx.mock
def test_asset_activate(invoke,
                        mock_asset_get_response,
                        item_type,
                        item_id,
                        asset_type_id,
                        dl_url):

    mock_asset_get_response()

    # Mock the response for activate_asset
    mock_resp_activate = httpx.Response(HTTPStatus.OK)
    respx.get(dl_url).return_value = mock_resp_activate

    runner = CliRunner()
    result = invoke(['asset-activate', item_type, item_id, asset_type_id],
                    runner=runner)

    assert not result.exception


@respx.mock
def test_asset_wait(invoke,
                    mock_asset_get_response,
                    item_type,
                    item_id,
                    asset_type_id,
                    dl_url):

    mock_asset_get_response()

    # Mock the response for wait_asset
    mock_resp_wait = httpx.Response(HTTPStatus.OK)
    respx.get(dl_url).return_value = mock_resp_wait

    runner = CliRunner()
    result = invoke(
        ['asset-wait', item_type, item_id, asset_type_id, '--delay', '0'],
        runner=runner)

    assert not result.exception
    assert "state: active" in result.output


# @respx.mock
# def test_asset_get(invoke):
#     item_type = 'PSScene'
#     item_id = '20221003_002705_38_2461xx'
#     asset_type_id = 'basic_udm2'
#     dl_url = f'{TEST_URL}/1?token=IAmAToken'

#     basic_udm2_asset = {
#         "_links": {
#             "_self": "SELFURL",
#             "activate": "ACTIVATEURL",
#             "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
#         },
#         "_permissions": ["download"],
#         "md5_digest": None,
#         "status": 'active',
#         "location": dl_url,
#         "type": "basic_udm2"
#     }

#     page_response = {
#         "basic_analytic_4b": {
#             "_links": {
#                 "_self":
#                 "SELFURL",
#                 "activate":
#                 "ACTIVATEURL",
#                 "type":
#                 "https://api.planet.com/data/v1/asset-types/basic_analytic_4b"
#             },
#             "_permissions": ["download"],
#             "md5_digest": None,
#             "status": "inactive",
#             "type": "basic_analytic_4b"
#         },
#         "basic_udm2": basic_udm2_asset
#     }

#     mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
#     assets_url = f'{TEST_URL}/item-types/{item_type}/items/{item_id}/assets'
#     respx.get(assets_url).return_value = mock_resp

#     runner = CliRunner()
#     result = invoke(['asset-get', item_type, item_id, asset_type_id],
#                     runner=runner)

#     assert not result.exception
#     assert json.dumps(basic_udm2_asset) in result.output

# TODO: basic test for "planet data search-list".
# TODO: basic test for "planet data search-run".
# TODO: basic test for "planet data item-get".
# TODO: basic test for "planet data stats".
