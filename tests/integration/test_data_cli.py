"""Tests of the Data CLI."""
from click.testing import CliRunner
import pytest
import json
import httpx
import respx
from http import HTTPStatus
from planet.cli import cli

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


def test_data_command_registered(invoke):
    """planet-data command prints help and usage message."""
    runner = CliRunner()
    result = invoke(["--help"], runner=runner)
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "search-quick" in result.output
    assert "search-create" in result.output
    # Add other sub-commands here.


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", ['{1:1}', '{"foo"}'])
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
def test_data_search_quick_filter_invalid_json(invoke, item_types, filter):
    """Test for planet data search_quick. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_QUICKSEARCH_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["search-quick", item_types, filter], runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
def test_data_search_quick_filter_success(invoke, item_types):
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
    result = invoke(["search-quick", item_types, json.dumps(filter)],
                    runner=runner)

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) == 1  # we have 1 feature


@respx.mock
@pytest.mark.parametrize("limit,limited_list_length", [(None, 100), (0, 102),
                                                       (1, 1)])
def test_data_search_quick_limit(invoke,
                                 search_results,
                                 limit,
                                 limited_list_length):
    """Test for planet data search_quick limit option. If no value is specified,
    make sure the result contains at most 100 entries."""
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
        ["search-quick", item_types, json.dumps(filter), "--limit", limit],
        runner=runner)
    assert result.exit_code == 0
    assert result.output.count('"id"') == limited_list_length


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", ['{1:1}', '{"foo"}'])
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
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
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
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
        '--daily_email'
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
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
def test_data_stats_filter_invalid_json(invoke, item_types, filter):
    """Test for planet data search_create. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_STATS_URL).return_value = mock_resp

    name = "temp"

    runner = CliRunner()
    result = invoke(["stats", name, item_types, filter], runner=runner)
    assert result.exit_code == 2


@respx.mock
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
def test_data_stats_filter_success(invoke, item_types):
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
    respx.post(TEST_STATS_URL).return_value = mock_resp

    runner = CliRunner()
    result = invoke(["search-create", name, item_types, json.dumps(filter)],
                    runner=runner)

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) == 1  # we have 1 feature
# TODO: basic test for "planet data filter".


# We expect this test to fail now. When the Data API client is
# available, we will remove the xfail marker and work to get this test,
# or a better version, to pass.
@pytest.mark.xfail(reason="Data client not yet implemented")
def test_search_quick():
    """planet data search-quick prints 1 GeoJSON Feature."""
    result = CliRunner().invoke(
        cli.main,
        # When testing, we "explode" our command and its parameters
        # into a list to make parameterization more clear.
        [
            "data",
            "search-quick",
            # To keep yapf from putting option name and value on
            # different lines, use a "=".
            "--limit=10",
            "--name=test",
            "--pretty",
            "lol,wut",
            "{}"
        ])
    assert result.exit_code == 0
    assert "Feature" in result.output


# TODO: basic test for "planet data search-create".
# TODO: basic test for "planet data search-update".
# TODO: basic test for "planet data search-delete".
# TODO: basic test for "planet data search-get".
# TODO: basic test for "planet data search-list".
# TODO: basic test for "planet data search-run".
# TODO: basic test for "planet data item-get".
# TODO: basic test for "planet data asset-activate".
# TODO: basic test for "planet data asset-wait".
# TODO: basic test for "planet data asset-download".
# TODO: basic test for "planet data stats".
