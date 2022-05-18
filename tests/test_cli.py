# Copyright 2017 Planet Labs, Inc.
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

from planet import api
from planet.api.__version__ import __version__
from planet.scripts import util
from planet.scripts import main
from planet.scripts import cli


# have to clear in case key is picked up via env
if api.auth.ENV_KEY in os.environ:
    os.environ.pop(api.auth.ENV_KEY)


client = MagicMock(name='client', spec=api.ClientV1)


def run_cli(*args, **kw):
    runner = CliRunner()
    return runner.invoke(main, *args, **kw)


def assert_success(result, expected):
    assert result.exit_code == 0
    assert json.loads(result.output) == json.loads(expected)


def assert_cli_exception(cause, expected):
    def thrower():
        raise cause
    try:
        util.call_and_wrap(thrower)
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
    assert None is util.read(None)
    assert 'foo' == util.read('foo')
    assert (1,) == util.read((1,))

    # same but with split
    assert None is util.read(None, split=True)
    assert ['foo'] == util.read('foo', split=True)
    assert (1,) == util.read((1,), split=True)

    # stdin specifiers
    with stdin('text'):
        assert 'text' == util.read('-')
    with stdin('text'):
        assert 'text' == util.read('@-')

    # explicit file specifier
    infile = tmpdir.join('infile')
    infile.write('farb')
    assert 'farb' == util.read('@%s' % infile)

    # implied file
    assert 'farb' == util.read('%s' % infile)

    # failed explict file
    try:
        noexist = 'not-here-hopefully'
        util.read('@%s' % noexist)
        assert False
    except ClickException as ex:
        assert str(ex) == "[Errno 2] No such file or directory: '%s'" % noexist

    # splitting
    xs = util.read(' x\nx\r\nx\t\tx\t\n x ', split=True)
    assert ['x'] * 5 == xs


def test_exception_translation():
    assert_cli_exception(api.exceptions.BadQuery('bogus'), 'BadQuery: bogus')
    assert_cli_exception(api.exceptions.APIException('911: alert'),
                         "Unexpected response: 911: alert")


def test_version_flag():
    results = run_cli(['--version'])
    assert results.output == "%s\n" % __version__


def test_workers_flag():
    assert 'workers' not in cli.client_params
    run_cli(['--workers', '19', 'help'])
    assert 'workers' in cli.client_params
    assert cli.client_params['workers'] == 19


def test_api_key_flag():
    run_cli(['-k', 'shazbot', 'help'])
    assert 'api_key' in cli.client_params
    assert cli.client_params['api_key'] == 'shazbot'


def test_get_terminal_size():
    """Check compatibility of get_terminal_size (see gh-529)."""
    columns, rows = util.get_terminal_size()
    assert isinstance(columns, int)
    assert isinstance(rows, int)
