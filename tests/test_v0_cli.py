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

import json
import os

from mock import MagicMock

from planet import api
from planet.api import models
from _common import read_fixture
from _common import clone

import pytest

pytestmark = pytest.mark.skipif(True, reason='v0 cli tests disabled')


def run_cli(): pass


def assert_success(): pass


# have to clear in case key is picked up via env
if api.auth.ENV_KEY in os.environ:
    os.environ.pop(api.auth.ENV_KEY)


client = MagicMock(name='client', spec=api.Client)


def test_search():

    expected = read_fixture('search.geojson')

    response = MagicMock(spec=models.JSON)
    response.get_raw.return_value = expected

    client.get_scenes_list.return_value = response

    result = run_cli(['search'])

    assert_success(result, expected)


def test_aoi_id_flag():
    run_cli(['search', '--aoi_id', 'dangbat'])
    client.get_scenes_list.assert_called_with(
        aoi_id='dangbat', count=1000, intersects=None, scene_type='ortho')


def test_search_by_aoi():

    aoi = read_fixture('search-by-aoi.geojson')
    expected = read_fixture('search-by-aoi.geojson')

    response = MagicMock(spec=models.JSON)
    response.get_raw.return_value = expected

    client.get_scenes_list.return_value = response

    # input kwarg simulates stdin
    result = run_cli(['search'], input=aoi)

    assert_success(result, expected)


def test_metadata():

    # Read in fixture
    expected = read_fixture('20150615_190229_0905.geojson')

    # Construct a response from the fixture
    response = MagicMock(spec=models.JSON)
    response.get_raw.return_value = expected

    # Construct the return response for the client method
    client.get_scene_metadata.return_value = response

    result = run_cli(['metadata', '20150615_190229_0905'])

    assert_success(result, expected)


def test_download():
    response = MagicMock(spec=models.Image)
    client.fetch_scene_geotiffs.return_value = response

    def test(ids, as_std_in=False):
        args, input = ['download'], None
        if as_std_in:
            input = '\n'.join(ids)
        else:
            args.extend(ids)
        assert_correct(run_cli(args, input=input), ids)

    def assert_correct(result, expected_ids):
        assert result.exit_code == 0
        called_with = client.fetch_scene_geotiffs.call_args[0]
        assert list(expected_ids) == list(called_with[0])
        assert 'ortho' == called_with[1]
        assert 'visual' == called_with[2]

    test(['20150615_190229_0905'])
    test(['20150615_190229_0905', '20150615_190229_0906'])
    test(['20150615_190229_0905'], as_std_in=True)
    test(['20150615_190229_0905', '20150615_190229_0906'], as_std_in=True)


def test_thumbs():
    response = MagicMock(spec=models.Image)
    client.fetch_scene_thumbnails.return_value = response

    def test(ids, as_std_in=False):
        args, input = ['thumbnails'], None
        if as_std_in:
            input = '\n'.join(ids)
        else:
            args.extend(ids)
        assert_correct(run_cli(args, input=input), ids)

    def assert_correct(result, expected_ids):
        assert result.exit_code == 0
        called_with = client.fetch_scene_thumbnails.call_args[0]
        assert list(expected_ids) == list(called_with[0])
        assert 'ortho' == called_with[1]
        assert 'md' == called_with[2]

    test(['20150615_190229_0905'])
    test(['20150615_190229_0905', '20150615_190229_0906'])
    test(['20150615_190229_0905'], as_std_in=True)
    test(['20150615_190229_0905', '20150615_190229_0906'], as_std_in=True)


def test_init():
    # monkey patch the storage file
    test_file = '.test_planet_json'
    api.utils._planet_json_file = lambda: test_file
    client.login.return_value = {
        'api_key': 'SECRIT'
    }
    try:
        result = run_cli(['init', '--email', 'bil@ly',
                          '--password', 'secret'])
        assert result.exit_code == 0
        assert os.path.exists(test_file)
        with open(test_file) as fp:
            data = json.loads(fp.read())
        assert data['key'] == 'SECRIT'
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


def test_mosaic_quads():
    response = MagicMock(spec=models.JSON)
    response.get_raw.return_value = '{"quads": []}'

    client.get_mosaic_quads.return_value = response
    result = run_cli(['mosaic-quads', 'some_mosaic_name'])
    assert result.exit_code == 0
    assert result.output == '{\n  "quads": []\n}\n'
    called_with = client.get_mosaic_quads.call_args[0]
    assert called_with[0] == 'some_mosaic_name'


def _set_workspace(workspace, *args, **kw):
    response = MagicMock(spec=models.JSON)
    response.get_raw.return_value = '{"status": "OK"}'

    client.set_workspace.return_value = response
    client.set_workspace.reset_mock()
    args = ['set-workspace'] + list(args)
    if workspace is not None:
        args += [json.dumps(workspace)]
    result = run_cli(args, input=kw.get('input', None))
    assert result.exit_code == kw.get('expected_status', 0)


def test_workspace_create_no_id():

    workspace = json.loads(read_fixture('workspace.json'))
    workspace.pop('id')
    expected = clone(workspace)
    _set_workspace(workspace)
    client.set_workspace.assert_called_once_with(expected, None)


def test_workspace_create_from_existing():

    workspace = json.loads(read_fixture('workspace.json'))
    expected = clone(workspace)
    _set_workspace(workspace, '--create')
    client.set_workspace.assert_called_once_with(expected, None)


def test_workspace_update_from_existing_with_id():

    workspace = json.loads(read_fixture('workspace.json'))
    expected = clone(workspace)
    _set_workspace(workspace, '--id', '12345')
    client.set_workspace.assert_called_once_with(expected, '12345')


def test_workspace_update_stdin():
    workspace = json.loads(read_fixture('workspace.json'))
    expected = clone(workspace)
    _set_workspace(workspace)
    client.set_workspace.assert_called_once_with(expected, workspace['id'])


def test_workspace_create_aoi_stdin():
    geometry = {'type': 'Point'}
    expected = {
        'name': 'foobar',
        'filters': {
            'geometry': {
                'intersects': geometry
            }
        }
    }

    # since the CLI wants to read from stdin for the 'workspace' arg,
    # provide an empty workspace
    _set_workspace({}, '--name', 'foobar', '--aoi', json.dumps(geometry))
    client.set_workspace.assert_called_once_with(expected, None)

    _set_workspace({}, '--name', 'foobar', '--aoi', '@-',
                   input=json.dumps(geometry))
    client.set_workspace.assert_called_once_with(expected, None)


def test_set_workspace_filters():
    _set_workspace({}, '--where', 'sat.id', 'eq', '0')
    expected = {
        'filters': {
            'sat.id': {
                'eq': '0'
            }
        }
    }
    client.set_workspace.assert_called_once_with(expected, None)
