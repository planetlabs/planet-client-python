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
from unittest.mock import Mock

import pytest

from planet.cli import io


@pytest.mark.parametrize(
    "pretty,expected",
    [(False, '{"key": "val"}'), (True, '{\n  "key": "val"\n}')])
def test_cli_echo_json(pretty, expected, monkeypatch):
    mock_echo = Mock()
    monkeypatch.setattr(io.click, 'echo', mock_echo)

    obj = {'key': 'val'}
    io.echo_json(obj, pretty)
    mock_echo.assert_called_once_with(expected)
