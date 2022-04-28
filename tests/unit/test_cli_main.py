# Copyright 2021 Planet Labs, PBC.
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
import logging

import pytest

import click
from click.testing import CliRunner

from planet.cli import cli

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def debug_input():
    return ['debug', ' debug ', 'debu', 45]


def test_cli_orders_quiet():

    runner = CliRunner()

    # Valid and invalid inputs for the "quiet" flag
    valid_quiet_inputs = ['--quiet', ' --quiet', ' --quiet ']
    invalid_quiet_inputs = ['--quiet ', '-q', '--not_a_valid_input', 123]

    # Test the valid quiet inputs
    for quiet_input in valid_quiet_inputs:
        valid_result = runner.invoke(cli.main, args=[quiet_input, 'orders'])
        assert not valid_result.exception
        assert valid_result.exit_code == 0
    # Test the invalid quiet inputs
    for quiet_input in invalid_quiet_inputs:
        invalid_result = runner.invoke(cli.main, args=[quiet_input, 'orders'])
        assert invalid_result.exception
        assert invalid_result.exit_code != 0


def test_cli_info_verbosity(monkeypatch):
    log_level = None

    # dummy command so we can invoke cli
    @click.command()
    def test():
        pass

    cli.main.add_command(test)

    def configtest(stream, level, format):
        nonlocal log_level
        log_level = level

    monkeypatch.setattr(cli.logging, 'basicConfig', configtest)

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['test'])
    assert result.exit_code == 0
    assert log_level == logging.WARNING

    def paramaterized_tests(debug_input):
        runner = CliRunner()
        result = runner.invoke(cli.main,
                               args=['--verbosity', debug_input, 'orders'])
        # Testing to ensure command was run succesfully and
        # \log_level set to debug
        if debug_input not in ['debug', ' debug ']:
            assert result.exit_code == 2
        else:
            assert result.exit_code == 0
            assert log_level == logging.DEBUG

    paramaterized_tests(debug_input)
