"""Tests of the Subscriptions CLI (aka planet-subscriptions)

There are 7 subscriptions commands:

[x] planet subscriptions cancel
[x] planet subscriptions create
[x] planet subscriptions get
[x] planet subscriptions list
[x] planet subscriptions patch
[x] planet subscriptions results
[x] planet subscriptions update

TODO: tests for 3 options of the planet-subscriptions-results command.

"""
import itertools
import json

from click.testing import CliRunner
import pytest

from planet.cli import cli

from test_subscriptions_api import (api_mock,
                                    cancel_mock,
                                    create_mock,
                                    failing_api_mock,
                                    get_mock,
                                    patch_mock,
                                    res_api_mock,
                                    update_mock,
                                    TEST_URL)

# CliRunner doesn't agree with empty options, so a list of option
# combinations which omit the empty options is best. For example,
# parametrizing 'limit' as '' and then executing
#
# CliRunner().invoke(cli.main, args=['subscriptions', 'list', limit]
#
# does not work.


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None, **kwargs):
        runner = runner or CliRunner()
        args = ['subscriptions', f'--base-url={TEST_URL}'] + extra_args
        return runner.invoke(cli.main, args=args, **kwargs)

    return _invoke


@pytest.mark.parametrize(
    'options,expected_count',
    [(['--status=running'], 100), ([], 100), (['--source-type=catalog'], 100),
     (['--source-type=soil_water_content'], 0),
     (['--limit=1', '--status=running'], 1),
     (['--limit=2', '--pretty', '--status=running'], 2),
     (['--limit=1', '--status=preparing'], 0),
     ([
         '--name=test xyz',
         '--name-contains=xyz',
         '--created=2018-02-12T00:00:00Z/..',
         '--updated=../2018-03-18T12:31:12Z',
         '--start-time=2018-01-01T00:00:00Z',
         '--end-time=2022-01-01T00:00:00Z/2024-01-01T00:00:00Z',
         '--hosting=true',
         '--sort-by=name DESC'
     ],
      2)])
@api_mock
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_list_options(invoke, options, expected_count):
    """Prints the expected sequence of subscriptions."""
    # While developing it is handy to have click's command invoker
    # *not* catch exceptions, so we can use the pytest --pdb option.
    result = invoke(['list'] + options, catch_exceptions=False)
    assert result.exit_code == 0  # success.

    # For a start, counting the number of "id" strings in the output
    # tells us how many subscription JSONs were printed, pretty or not.
    assert result.output.count('"id"') == expected_count


@failing_api_mock
def test_subscriptions_create_failure(invoke):
    """An invalid subscription request fails to create a new subscription."""
    # This subscription request lacks the required "delivery" and
    # "source" members.
    sub = {'name': 'lol'}

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', '-'],
        input=json.dumps(sub),
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.
    assert "Error:" in result.output


# This subscription request has the members required by our fake API.
# It must be updated when we begin to test against a more strict
# imitation of the Planet Subscriptions API.
GOOD_SUB_REQUEST = {'name': 'lol', 'delivery': True, 'source': 'wut'}
GOOD_SUB_REQUEST_WITH_HOSTING = {
    'name': 'lol', 'source': 'wut', 'hosting': True
}


@pytest.mark.parametrize('cmd_arg, runner_input',
                         [('-', json.dumps(GOOD_SUB_REQUEST)),
                          (json.dumps(GOOD_SUB_REQUEST), None),
                          ('-', json.dumps(GOOD_SUB_REQUEST_WITH_HOSTING)),
                          (json.dumps(GOOD_SUB_REQUEST_WITH_HOSTING), None)])
@create_mock
def test_subscriptions_create_success(invoke, cmd_arg, runner_input):
    """Subscriptions creation succeeds with a valid subscription request."""

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


# Invalid JSON.
BAD_SUB_REQUEST = '{0: "lolwut"}'


@pytest.mark.parametrize('cmd_arg, runner_input', [('-', BAD_SUB_REQUEST),
                                                   (BAD_SUB_REQUEST, None)])
def test_subscriptions_bad_request(invoke, cmd_arg, runner_input):
    """Short circuit and print help message if request is bad."""
    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 2  # bad parameter.


@failing_api_mock
def test_subscriptions_cancel_failure(invoke):
    """Cancel command exits gracefully from an API error."""
    result = invoke(
        ['cancel', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@cancel_mock
def test_subscriptions_cancel_success(invoke):
    """Cancel command succeeds."""
    result = invoke(
        ['cancel', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


@failing_api_mock
def test_subscriptions_update_failure(invoke):
    """Update command exits gracefully from an API error."""
    result = invoke(
        ['update', 'test', json.dumps(GOOD_SUB_REQUEST)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@update_mock
def test_subscriptions_update_success(invoke):
    """Update command succeeds."""
    request = GOOD_SUB_REQUEST.copy()
    request['name'] = 'new_name'

    result = invoke(
        ['update', 'test', json.dumps(request)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['name'] == 'new_name'


@failing_api_mock
def test_subscriptions_patch_failure(invoke):
    """Patch command exits gracefully from an API error."""
    result = invoke(
        ['patch', 'test', json.dumps(GOOD_SUB_REQUEST)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@patch_mock
def test_subscriptions_patch_success(invoke):
    """Patch command succeeds."""
    request = {'name': 'test patch'}
    result = invoke(
        ['patch', 'test', json.dumps(request)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['name'] == request['name']


@failing_api_mock
def test_subscriptions_get_failure(invoke):
    """Describe command exits gracefully from an API error."""
    result = invoke(
        ['get', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@get_mock
def test_subscriptions_get_success(invoke):
    """Describe command succeeds."""
    result = invoke(
        ['get', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['id'] == '42'


@failing_api_mock
def test_subscriptions_results_failure(invoke):
    """Results command exits gracefully from an API error."""
    result = invoke(
        ['results', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@pytest.mark.parametrize('options,expected_count',
                         [(['--status=created'], 100), ([], 100),
                          (['--limit=1', '--status=created'], 1),
                          (['--limit=2', '--pretty', '--status=created'], 2),
                          (['--limit=1', '--status=queued'], 0)])
@res_api_mock
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_results_success(invoke, options, expected_count):
    """Describe command succeeds."""
    result = invoke(
        ['results', 'test'] + options,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert result.output.count('"id"') == expected_count


def test_request_base_success(invoke, geom_geojson):
    """Request command succeeds."""
    source = json.dumps({
        "type": "catalog",
        "parameters": {
            "geometry": geom_geojson,
            "start_time": "2021-03-01T00:00:00Z",
            "end_time": "2023-11-01T00:00:00Z",
            "rrule": "FREQ=MONTHLY;BYMONTH=3,4,5,6,7,8,9,10",
            "item_types": ["PSScene"],
            "asset_types": ["ortho_analytic_4b"]
        }
    })
    delivery = json.dumps({
        "type": "amazon_s3",
        "parameters": {
            "aws_access_key_id": "keyid",
            "aws_secret_access_key": "accesskey",
            "bucket": "bucket",
            "aws_region": "region"
        }
    })

    result = invoke([
        'request',
        '--name=test',
        f'--source={source}',
        f'--delivery={delivery}'
    ])

    assert source in result.output
    assert result.exit_code == 0  # success.


@pytest.mark.parametrize("geom_fixture",
                         [('geom_geojson'), ('geom_reference'),
                          ("str_geom_reference")])
def test_request_base_clip_to_source(geom_fixture, request, invoke):
    """Clip to source using command line option."""
    geom = request.getfixturevalue(geom_fixture)
    source = json.dumps({
        "type": "catalog",
        "parameters": {
            "geometry": geom,
            "start_time": "2021-03-01T00:00:00Z",
            "item_types": ["PSScene"],
            "asset_types": ["ortho_analytic_4b"],
        },
    })
    result = invoke([
        'request',
        '--name=test',
        f'--source={source}',
        '--delivery={"type": "fake"}',
        '--clip-to-source'
    ])

    assert result.exit_code == 0  # success.
    req = json.loads(result.output)
    tool = req["tools"][0]
    assert tool["type"] == "clip"
    assert tool["parameters"]["aoi"] == geom


def test_request_catalog_success(invoke, geom_geojson):
    """Request-catalog command succeeds"""
    source = {
        "type": "catalog",
        "parameters": {
            "geometry": geom_geojson,
            "start_time": "2021-03-01T00:00:00Z",
            "item_types": ["PSScene"],
            "asset_types": ["ortho_analytic_4b"]
        }
    }

    result = invoke([
        'request-catalog',
        '--item-types=PSScene',
        '--asset-types=ortho_analytic_4b',
        f"--geometry={json.dumps(geom_geojson)}",
        '--start-time=2021-03-01T00:00:00'
    ])
    assert json.loads(result.output) == source
    assert result.exit_code == 0  # success.


@res_api_mock
def test_subscriptions_results_csv(invoke):
    """Get results as CSV."""
    result = invoke(["results", "test", "--csv"])
    assert result.exit_code == 0  # success.
    assert result.output.splitlines() == ["id,status", "1234-abcd,SUCCESS"]


@pytest.mark.parametrize(
    "geom", ["geom_geojson", "geom_reference", "str_geom_reference"])
def test_request_pv_success(invoke, geom, request):
    """Request-pv command succeeds"""
    geom = request.getfixturevalue(geom)
    if isinstance(geom, dict):
        geom = json.dumps(geom)
    result = invoke([
        "request-pv",
        "--var-type=biomass_proxy",
        "--var-id=BIOMASS-PROXY_V3.0_10",
        f"--geometry={geom}",
        "--start-time=2021-03-01T00:00:00",
    ])

    assert result.exit_code == 0  # success.
    source = json.loads(result.output)
    assert source["type"] == "biomass_proxy"
    assert source["parameters"]["id"] == "BIOMASS-PROXY_V3.0_10"


@pytest.mark.parametrize(
    # Test all the combinations of the three options plus some with dupes.
    "publishing_stages",
    list(
        itertools.chain.from_iterable(
            itertools.combinations(["preview", "standard", "finalized"], i)
            for i in range(1, 4))) + [("preview", "preview"),
                                      ("preview", "finalized", "preview")])
def test_catalog_source_publishing_stages(invoke,
                                          geom_geojson,
                                          publishing_stages):
    """Catalog source publishing stages are configured."""
    result = invoke([
        'request-catalog',
        '--item-types=PSScene',
        '--asset-types=ortho_analytic_4b',
        f"--geometry={json.dumps(geom_geojson)}",
        '--start-time=2021-03-01T00:00:00',
    ] + [f'--publishing-stage={stage}' for stage in publishing_stages])

    assert result.exit_code == 0  # success.
    req = json.loads(result.output)
    assert req['parameters']['publishing_stages'] == list(
        set(publishing_stages))


@pytest.mark.parametrize("time_range_type", ["acquired", "published"])
def test_catalog_source_time_range_type(invoke, geom_geojson, time_range_type):
    """Catalog source time range type is configured."""
    result = invoke([
        'request-catalog',
        '--item-types=PSScene',
        '--asset-types=ortho_analytic_4b',
        f"--geometry={json.dumps(geom_geojson)}",
        '--start-time=2021-03-01T00:00:00',
        f'--time-range-type={time_range_type}',
    ])

    assert result.exit_code == 0  # success.
    req = json.loads(result.output)
    assert req['parameters']['time_range_type'] == time_range_type


@pytest.mark.parametrize(
    "hosting_option, collection_id_option, expected_success",
    [
        ("--hosting=sentinel_hub", None, True),
        ("--hosting=sentinel_hub",
         "--collection-id=7ff105c4-e0de-4910-96db-8345d86ab734",
         True),
    ])
def test_request_hosting(invoke,
                         geom_geojson,
                         hosting_option,
                         collection_id_option,
                         expected_success):
    """Test request command with various hosting and collection ID options."""
    source = json.dumps({
        "type": "catalog",
        "parameters": {
            "geometry": geom_geojson,
            "start_time": "2021-03-01T00:00:00Z",
            "end_time": "2023-11-01T00:00:00Z",
            "rrule": "FREQ=MONTHLY;BYMONTH=3,4,5,6,7,8,9,10",
            "item_types": ["PSScene"],
            "asset_types": ["ortho_analytic_4b"]
        }
    })

    cmd = [
        'request',
        '--name=test',
        f'--source={source}',
        hosting_option,
    ]

    if collection_id_option:
        cmd.append(collection_id_option)

    result = invoke(cmd)

    assert result.exit_code == 0, "Expected command to succeed."
