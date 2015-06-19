# Copyright 2015 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

import planet
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
    except ClickException as ex:
        print("HERE")
        # print(str(ex))
        assert str(ex) == expected


def test_exception_translation():
    assert_cli_exception(api.BadQuery('bogus'), 'BadQuery: bogus')
    assert_cli_exception(api.APIException('911: alert'),
                         "Unexpected response: 911: alert")


def test_version_flag():

    results = runner.invoke(scripts.cli, ['--version'])
    assert results.output == "%s\n" % planet.__version__


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


def test_search_by_aoi():

    aoi_path = os.path.join(FIXTURE_DIR, 'aoi.geojson')
    with open(aoi_path, 'r') as src:
        aoi = src.read()

    fixture_path = os.path.join(FIXTURE_DIR, 'search-by-aoi.geojson')
    with open(fixture_path, 'r') as src:
        expected = src.read()

    response = MagicMock(spec=api.JSON)
    response.get_raw.return_value = expected

    scripts.client.get_scenes_list.return_value = response

    # input kwarg simulates stdin
    result = runner.invoke(scripts.cli, ['search'], input=aoi)

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

