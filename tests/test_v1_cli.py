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
        try:
            expected_output = json.loads(expected_output)
        except ValueError:
            pass
    try:
        assert json.loads(result.output) == expected_output
    except:
        assert result.output == expected_output


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
        filt('--filter-json {"foo":true}'),
        '"--filter-json": Does not appear to be valid filter'
    )
    assert_failure(
        filt('--filter-json @not-file'),
        # @todo this is not a nice errror - see note in 'util:read'
        'Error: [Errno 2] No such file or directory: \'not-file\''
    )


def configure_response(func, raw, body=models.JSON):
    body = MagicMock(name='body', spec=body)
    body.get_raw.return_value = raw
    body.get.return_value = json.loads(raw)
    func.return_value = body


def test_quick_search(runner, client):
    fake_response = '{"chowda":true}'
    configure_response(client.quick_search, fake_response)
    assert_success(
        runner.invoke(main, [
            'quick-search', '--item-type', 'all', '--limit', '1'
        ]), fake_response)
    assert client.quick_search.call_args[1]['page_size'] == 1


def test_download_errors(runner):
    '''test download cli error handling'''
    def download(opts):
        return runner.invoke(main, ['download'] + opts.split(' '))
    assert_failure(
        download(('--search-id foobar --asset-type visual --item-type all'
                  ' --string-in a b')),
        'search options not supported with saved search'
    )
    assert_failure(
        download(('--search-id foobar --asset-type visual --item-type all'
                  ' --dry-run')),
        'dry-run not supported with saved search'
    )
    assert_failure(
        download(('--asset-type visual --item-type all'
                  ' --dry-run')),
        'dry-run not supported with open query'
    )


def test_download_dry_run(runner, client, monkeypatch):
    configure_response(client.stats,
                       '{"buckets": [{"count": 1}, {"count": 2}]}')
    assert_success(
        runner.invoke(main, [
            'download', '--asset-type', 'visual*', '--item-type', 'all',
            '--dry-run', '--string-in', 'foo', 'xyz'
        ]), 'would download approximately 6 assets from 3 items\n')


def test_download_quick(runner, client, monkeypatch):
    resp = MagicMock('response')
    resp.items_iter = lambda x: None
    client.quick_search.return_value = resp
    dl = MagicMock(name='downloader')
    monkeypatch.setattr('planet.scripts.v1.downloader', dl)
    monkeypatch.setattr('planet.scripts.v1.monitor_stats',
                        lambda *a, **kw: None)
    monkeypatch.setattr('planet.scripts.v1.handle_interrupt',
                        lambda *a, **kw: None)
    assert_success(
        runner.invoke(main, [
            'download', '--asset-type', 'visual', '--item-type', 'all',
            '--limit', '1'
        ]), '')
    assert client.quick_search.call_args[1]['page_size'] == 1


def test_create_search(runner, client):
    fake_response = '{"chowda":true}'
    configure_response(client.create_search, fake_response)
    assert_success(
        runner.invoke(main, [
            'create-search', '--item-type', 'all', '--name', 'new-search'
        ]), fake_response)


def test_geom_filter(runner, client):
    geom = json.dumps({
        'type': 'Point',
        'coordinates': [100, 100]
    })
    fake_response = '{"chowda":true}'
    configure_response(client.create_search, fake_response)
    assert_success(
        runner.invoke(main, [
            'create-search', '--item-type', 'all', '--name', 'new-search',
            '--geom', geom
        ]), fake_response)
    args, kw = client.create_search.call_args
    req = args[0]
    assert req['filter']['config'][0]['type'] == 'GeometryFilter'
