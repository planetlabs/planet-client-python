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
    result = invoke(["--help"], runner = runner)
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "search-quick" in result.output
    # Add other sub-commands here.


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("filter", [{''}, {"foo"}])
@pytest.mark.parametrize(
    "item_types", ['PSScene', 'SkySatScene', ('PSScene', 'SkySatScene')])
def test_data_search_quick_filter_fail(invoke, item_types, filter):
    """Test for planet data search_quick. Test with multiple item_types.
    Test should fail as filter does not contain valid JSON."""
    mock_resp = httpx.Response(HTTPStatus.OK,
                               json={'features': [{
                                   "key": "value"
                               }]})
    respx.post(TEST_QUICKSEARCH_URL).return_value = mock_resp

    runner = CliRunner()
    item_types = 'SkySatScene'
    with pytest.raises(TypeError):
        result = invoke(["search-quick", item_types, json.dumps(filter)],
                        runner=runner)


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
