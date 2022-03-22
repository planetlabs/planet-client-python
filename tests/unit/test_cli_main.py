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

    def test_loggingoutput_normal(capfd):
        # test a normal case
        runner = CliRunner()
        result = runner.invoke(cli.main,
                               args=['--verbosity', 'debug', 'orders'],
                               catch_exceptions=True)
        assert "Commands for interacting with the Orders API" in result.output

    def test_loggingoutput_space(capfd):
        # test a case with extra spaces (should still work)
        runner = CliRunner()
        result = runner.invoke(cli.main,
                               args=['--verbosity', ' debug ', 'orders'],
                               catch_exceptions=True)
        assert "Commands for interacting with the Orders API" in result.output

    def test_loggingoutput_misspell(capfd):
        # test a case where the argument is misspelled
        runner = CliRunner()
        result = runner.invoke(cli.main,
                               args=['--verbosity', 'debu', 'orders'],
                               catch_exceptions=True)
        assert "please set verbosity" in str(result.exception)

    def test_loggingoutput_number(capfd):
        # test a case when input includes number instead of string
        runner = CliRunner()
        result = runner.invoke(cli.main,
                               args=['--verbosity', 45, 'orders'],
                               catch_exceptions=True)
        assert "please set verbosity" in str(result.exception)

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['test'])
    assert result.exit_code == 0
    assert log_level == logging.WARNING
