# Copyright 2022 Planet Labs, PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
from contextlib import nullcontext as does_not_raise
from datetime import datetime
import json

import click
from click.testing import CliRunner
from click.exceptions import BadParameter
import pytest

from planet.cli import types


@pytest.mark.parametrize("input,expectation, expected",
                         [('a', does_not_raise(), ['a']),
                          ('a,b', does_not_raise(), ['a', 'b']),
                          ('a, b', does_not_raise(), ['a', 'b']),
                          ('a,,', pytest.raises(BadParameter), None),
                          ('', pytest.raises(BadParameter), None),
                          (['a'], does_not_raise(), ['a'])])  # yapf: disable
def test_cli_CommaSeparatedString(input, expectation, expected):
    with expectation:
        res = types.CommaSeparatedString().convert(input, None, None)

    if expected:
        assert res == expected


@pytest.mark.parametrize("input, expectation, expected",
                         [
                             ('1.0', does_not_raise(), [1.0]),
                             ('1,2.5', does_not_raise(), [1.0, 2.5]),
                             ('1, 2.5', does_not_raise(), [1.0, 2.5]),
                             ('foo, bar', pytest.raises(BadParameter), None),
                             ('1,,', pytest.raises(BadParameter), None),
                             ([1.0, 2.0], does_not_raise(), [1.0, 2.0]),
                         ])
def test_cli_CommaSeparatedFloat(input, expectation, expected):
    with expectation:
        res = types.CommaSeparatedFloat().convert(input, None, None)

    if expected:
        assert res == expected


@pytest.fixture(params=["stdin", "str", "file"])
def json_input_test_params(request, write_to_tmp_json_file):

    def _func(input_json):
        if request.param == 'file':
            filename = write_to_tmp_json_file(input_json, 'tmp.json')
            arg = str(filename)
            input = None
        elif request.param == 'str':
            arg = json.dumps(input_json)
            input = None
        elif request.param == 'stdin':
            arg = '-'
            input = json.dumps(input_json)

        return arg, input

    return _func


def test_cli_JSON_inputs(json_input_test_params):
    """Confirm that file, stdin, and str inputs are all supported"""

    @click.option('--foo', type=types.JSON())
    @click.command()
    def test(foo):
        click.echo(json.dumps(foo))

    test_json = {'a': 'b'}
    arg, input = json_input_test_params(test_json)
    result = CliRunner().invoke(test, args=[f'--foo={arg}'], input=input)
    assert result.exit_code == 0
    assert json.loads(result.output) == test_json


parametrize_json = pytest.mark.parametrize(
    "input, expectation, expected",
    [
        ('{"a":["b", "c"], "c":5}',
         does_not_raise(), {
             'a': ['b', 'c'], 'c': 5
         }),
        ('["b", {"c":5}]', does_not_raise(), ['b', {
            'c': 5
        }]),
        ('{"a":"b", foo:bar}', pytest.raises(BadParameter), None),
        ('{}', pytest.raises(BadParameter), None),
    ])


@parametrize_json
def test_cli_JSON_str(input, expectation, expected):
    with expectation:
        res = types.JSON().convert(input, None, None)

    if expected:
        assert res == expected


@parametrize_json
def test_cli_JSON_file_content(input, expectation, expected, tmp_path):
    filename = tmp_path / 'temp.json'
    with open(filename, 'w') as fp:
        fp.write(input)

    with expectation:
        res = types.JSON().convert(str(filename), None, None)

    if expected:
        assert res == expected


def test_cli_JSON_file_doesnotexist():
    with pytest.raises(BadParameter):
        types.JSON().convert('nonexistant.json', None, None)


@pytest.mark.parametrize("input, expectation",
                         [('gt', does_not_raise()), ('lt', does_not_raise()),
                          ('foobar', pytest.raises(BadParameter))])
def test_cli_Comparison(input, expectation):
    with expectation:
        res = types.Comparison().convert(input, None, None)
        assert res == input


@pytest.mark.parametrize("input, expectation",
                         [('gt', does_not_raise()),
                          ('lt', pytest.raises(BadParameter)),
                          ('foobar', pytest.raises(BadParameter))])
def test_cli_GTComparison(input, expectation):
    with expectation:
        res = types.GTComparison().convert(input, None, None)
        assert res == input


@pytest.mark.parametrize(
    "input, expectation, expected",
    [('2020-02-02', does_not_raise(), datetime(2020, 2, 2)),
     ('2021-02-03T01:40:07.359Z',
      does_not_raise(),
      datetime(2021, 2, 3, 1, 40, 7, 359000)),
     ('2022', pytest.raises(BadParameter), None),
     (datetime(2020, 2, 2), does_not_raise(), datetime(2020, 2, 2))])
def test_cli_DateTime(input, expectation, expected):
    with expectation:
        res = types.DateTime().convert(input, None, None)

    if expected:
        assert res == expected
