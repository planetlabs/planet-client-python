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


parametrize_json = pytest.mark.parametrize("input, expectation, expected", [
    ('{"a":["b", "c"], "c":5}', does_not_raise(), {'a': ['b', 'c'], 'c': 5}),
    ('["b", {"c":5}]', does_not_raise(), ['b', {'c': 5}]),
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
