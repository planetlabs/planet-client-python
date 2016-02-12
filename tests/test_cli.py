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

from contextlib import contextmanager
import json
import os
import sys
try:
    from StringIO import StringIO as Buffy
except ImportError:
    from io import BytesIO as Buffy

from click import ClickException
from click.testing import CliRunner

from mock import MagicMock
from mock import patch

import planet
from planet import api
from planet.api import models
from planet import scripts
from _common import read_fixture
from _common import clone


# have to clear in case key is picked up via env
if api.auth.ENV_KEY in os.environ:
    os.environ.pop(api.auth.ENV_KEY)


client = MagicMock(name='client', spec=api.Client)


def run_cli(*args, **kw):
    runner = CliRunner()
    with patch('planet.scripts.client', lambda: client):
        return runner.invoke(scripts.cli, *args, **kw)


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
        assert str(ex) == expected


@contextmanager
def stdin(content):
    saved = sys.stdin
    sys.stdin = Buffy(content.encode('utf-8'))
    yield
    sys.stdin = saved


def test_read(tmpdir):
    # no special files in arguments, expect what's been passed in
    assert None is scripts.read(None)
    assert 'foo' == scripts.read('foo')
    assert (1,) == scripts.read((1,))

    # same but with split
    assert None is scripts.read(None, split=True)
    assert ['foo'] == scripts.read('foo', split=True)
    assert (1,) == scripts.read((1,), split=True)

    # stdin specifiers
    with stdin('text'):
        assert 'text' == scripts.read('-')
    with stdin('text'):
        assert 'text' == scripts.read('@-')

    # explicit file specifier
    infile = tmpdir.join('infile')
    infile.write('farb')
    assert 'farb' == scripts.read('@%s' % infile)

    # implied file
    assert 'farb' == scripts.read('%s' % infile)

    # failed explict file
    try:
        noexist = 'not-here-hopefully'
        scripts.read('@%s' % noexist)
        assert False
    except ClickException as ex:
        assert str(ex) == "[Errno 2] No such file or directory: '%s'" % noexist

    # splitting
    xs = scripts.read(' x\nx\r\nx\t\tx\t\n x ', split=True)
    assert ['x'] * 5 == xs


def test_exception_translation():
    assert_cli_exception(api.exceptions.BadQuery('bogus'), 'BadQuery: bogus')
    assert_cli_exception(api.exceptions.APIException('911: alert'),
                         "Unexpected response: 911: alert")


def test_version_flag():

    results = run_cli(['--version'])
    assert results.output == "%s\n" % planet.__version__


def test_workers_flag():
    assert 'workers' not in scripts.client_params
    run_cli(['--workers', '19', 'search'])
    assert 'workers' in scripts.client_params
    assert scripts.client_params['workers'] == 19


def test_api_key_flag():
    run_cli(['-k', 'shazbot', 'search'])
    assert 'api_key' in scripts.client_params
    assert scripts.client_params['api_key'] == 'shazbot'


def test_no_api_key():
    runner = CliRunner()

    def assert_no_api_key(*args):
        result = runner.invoke(scripts.cli, *args)
        assert result.exit_code != 0
        assert 'Error: InvalidAPIKey: No API key provided\n' == result.output
        return True

    # the following should all fail w/ the same error
    assert all(map(assert_no_api_key, [
        ('search',),
        ('metadata', 'whatever'),
        ('download', 'whatever'),
        ('thumbnails', 'whatever'),
        ('mosaic-quads', 'whatever'),
        ('list-workspaces',),
    ]))


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
