# # Copyright 2021 Planet Labs, Inc.
# #
# # Licensed under the Apache License, Version 2.0 (the "License"); you may not
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
import logging
from unittest.mock import MagicMock

from click.testing import CliRunner
import pytest

import planet
from planet.scripts.cli import cli

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def runner():
    return CliRunner()


def test_auth_init_bad_pw(runner, monkeypatch):
    def invalidapikey(*args, **kwargs):
        raise planet.api.exceptions.InvalidAPIKey

    monkeypatch.setattr(planet.Auth, 'from_login', invalidapikey)
    result = runner.invoke(cli, args=['auth', 'init'], input='email\npw\n')
    assert 'Error: Invalid email or password.' in result.output


def test_auth_init_bad_email(runner, monkeypatch):
    def badquery(*args, **kwargs):
        raise planet.api.exceptions.BadQuery

    monkeypatch.setattr(planet.Auth, 'from_login', badquery)
    result = runner.invoke(cli, args=['auth', 'init'], input='email\npw\n')
    assert 'Error: Not a valid email address.' in result.output


def test_auth_init_success(runner, monkeypatch):
    mock_api_auth = MagicMock(spec=planet.auth.APIKeyAuth)
    mock_auth = MagicMock(spec=planet.Auth)
    mock_auth.from_login.return_value = mock_api_auth
    monkeypatch.setattr(planet, 'Auth', mock_auth)

    result = runner.invoke(cli, args=['auth', 'init'], input='email\npw\n')
    mock_auth.from_login.assert_called_once()
    mock_api_auth.write.assert_called_once()
    assert 'Initialized' in result.output


def test_auth_value_failure(runner, monkeypatch):
    def authexception(*args, **kwargs):
        raise planet.auth.AuthException

    monkeypatch.setattr(planet.Auth, 'from_file', authexception)

    result = runner.invoke(cli, ['auth', 'value'])
    assert 'Error: Auth information does not exist or is corrupted.' \
        in result.output


def test_auth_value_success(runner):
    result = runner.invoke(cli, ['auth', 'value'])
    assert not result.exception
    assert result.output == 'testkey\n'
