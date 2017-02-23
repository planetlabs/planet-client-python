from click.testing import CliRunner
import json
import os
import traceback
from mock import MagicMock
from mock import patch
from planet import api
from planet.scripts import main
from planet.api import ClientV1
from planet.api import models
import pytest

# have to clear in case key is picked up via env
if api.auth.ENV_KEY in os.environ:
    os.environ.pop(api.auth.ENV_KEY)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def client():
    client = MagicMock(name='client', spec=ClientV1)
    with patch('planet.scripts.v1.clientv1', lambda: client):
        yield client


def assert_success(result, expected_output, exit_code=0):
    if result.exception:
        print(result.output)
        raise Exception(traceback.format_tb(result.exc_info[2]))
    assert result.exit_code == exit_code, result.output
    if not isinstance(expected_output, dict):
        expected_output = json.loads(expected_output)
    assert json.loads(result.output) == expected_output


def assert_failure(result, error):
    assert result.exit_code != 0
    assert error in result.output


def test_filter(runner):
    def filt(*opts):
        return runner.invoke(main, ['filter'] + list(opts))
    assert_success(filt(), {
        "type": "AndFilter",
        "config": []
    })
    assert_success(filt('--string-in', 'eff', 'a b c'), {
        "type": "AndFilter",
        "config": [
            {'config': ['a', 'b', 'c'], 'field_name': 'eff',
             'type': 'StringInFilter'}
        ]
    })
    # @todo more cases that are easier to write/maintain


def test_filter_options_invalid(runner):
    # these will exercise much of the general filter failure paths for filter
    # options used across commands

    def filt(opts):
        return runner.invoke(main, ['filter'] + opts.split(' '))

    assert_failure(
        filt('--number-in a a'),
        '"--number-in": invalid value: a'
    )
    assert_failure(
        filt('--date a a a'),
        '"--date": invalid operator: a. allowed: lt,lte,gt,gte'
    )
    assert_failure(
        filt('--date a lt a'),
        '"--date": invalid date: a.'
    )
    assert_failure(
        filt('--range a a a'),
        '"--range": invalid operator: a. allowed: lt,lte,gt,gte'
    )
    assert_failure(
        filt('--geom not-geojson'),
        '"--geom": invalid GeoJSON'
    )
    assert_failure(
        filt('--geom @not-file'),
        # @todo this is not a nice errror - see note in 'util:read'
        'Error: [Errno 2] No such file or directory: \'not-file\''
    )
    assert_failure(
        filt('--filter-json not-json'),
        '"--filter-json": invalid JSON'
    )
    assert_failure(
        filt('--filter-json @not-file'),
        # @todo this is not a nice errror - see note in 'util:read'
        'Error: [Errno 2] No such file or directory: \'not-file\''
    )


def configure_response(func, raw, body=models.JSON):
    body = MagicMock(name='body', spec=body)
    body.get_raw.return_value = raw
    func.return_value = body


def test_quick_search(runner, client):
    fake_response = '{"chowda":true}'
    configure_response(client.quick_search, fake_response)
    assert_success(
        runner.invoke(main, [
            'quick-search', '--item-type', 'all', '--limit', '1'
        ]), fake_response)


def test_create_search(runner, client):
    fake_response = '{"chowda":true}'
    configure_response(client.create_search, fake_response)
    assert_success(
        runner.invoke(main, [
            'create-search', '--item-type', 'all', '--name', 'new-search'
        ]), fake_response)
