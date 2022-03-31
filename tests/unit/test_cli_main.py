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
    
    #TODO: Parametrize below tests
    #TODO: Check for writing to stderr

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['--verbosity', 'debug', 'test'])
    # Testing to ensure command was run succesfully and log_level set to debug
    assert result.exit_code == 0
    assert log_level == logging.DEBUG

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['--verbosity', ' debug ', 'test'])
    # test a case with extra spaces (should still work)
    assert result.exit_code == 0
    assert log_level == logging.DEBUG

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['--verbosity', 'debu', 'test'])
    # test a case where argument is mis-spelled
    assert result.exit_code == 2

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['--verbosity', 45, 'test'])
    # test a case when input includes number instead of string
    assert result.exit_code == 2
