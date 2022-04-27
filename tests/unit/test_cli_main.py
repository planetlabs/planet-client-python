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

import click
from click.testing import CliRunner

from planet.cli import cli

LOGGER = logging.getLogger(__name__)


def test_cli_orders_quiet():

    runner = CliRunner()

    # Dummy valid and invalid inputs for the "quiet" flag
    valid_quiet_inputs = ['-q', ' --quiet ']
    invalid_quiet_inputs = ['--not_a_valid_input', 123]

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


# TODO: when testing multiple values for verbosity, use test parameterization
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
