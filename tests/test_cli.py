'''
Command line specific tests - the client should be completely mocked and the
focus should be on asserting any CLI logic prior to client method invocation

lower level lib/client tests go in the test_mod suite
'''

import os
import json

from click import ClickException
from click.testing import CliRunner

from mock import MagicMock

from planet import api
from planet import scripts


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIR = os.path.join(TEST_DIR, 'fixtures')

scripts.client = MagicMock(name='client', spec=api.Client)
runner = CliRunner()


def assert_success(result, expected):
    assert result.exit_code == 0
    assert json.loads(result.output) == json.loads(expected)


def assert_cli_exception(cause, expected):
    def thrower():
        raise cause
    try:
        scripts.call_and_wrap(thrower)
        assert False, 'did not throw'
    except ClickException, ex:
        assert ex.message == expected


def test_exception_translation():
    assert_cli_exception(api.BadQuery('bogus'), 'BadQuery: bogus')
    assert_cli_exception(api.APIException('911: alert'),
                         "Unexpected response: 911: alert")


def test_list_scene_types():
    
    fixture_path = os.path.join(FIXTURE_DIR, 'scene-types.json')
    with open(fixture_path, 'r') as src:
        expected = src.read()
    
    response = MagicMock(spec=api.JSON)
    response.get_raw.return_value = expected
    
    scripts.client.list_scene_types.return_value = response
    
    result = runner.invoke(scripts.cli, ['list-scene-types'])
    
    assert_success(result, expected)


def test_search():
    
    fixture_path = os.path.join(FIXTURE_DIR, 'search.geojson')
    with open(fixture_path, 'r') as src:
        expected = src.read()
    
    response = MagicMock(spec=api.JSON)
    response.get_raw.return_value = expected
    
    scripts.client.get_scenes_list.return_value = response
    
    result = runner.invoke(scripts.cli, ['search'])
    
    assert_success(result, expected)
    

def test_metadata():
    
    # Read in fixture
    fixture_path = os.path.join(FIXTURE_DIR, '20150615_190229_0905.geojson')
    with open(fixture_path, 'r') as src:
        expected = src.read()
    
    # Construct a response from the fixture
    response = MagicMock(spec=api.JSON)
    response.get_raw.return_value = expected
    
    # Construct the return response for the client method
    scripts.client.get_scene_metadata.return_value = response

    result = runner.invoke(scripts.cli, ['metadata', '20150615_190229_0905'])

    assert_success(result, expected)

