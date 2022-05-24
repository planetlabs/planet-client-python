# Copyright 2021 Planet Labs PBC.
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

from unittest import mock
from planet.cli import cli

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize("option,quiet", [("", False), ("--quiet", True)])
def test_cli_orders_quiet(option, quiet):
    """Check that --quiet is passed in context to subcommands."""

    # dummy command so we can invoke cli
    @click.command()
    @click.pass_context
    def test(ctx):
        assert ctx.obj['QUIET'] is quiet

    cli.main.add_command(test)

    runner = CliRunner()
    runner.invoke(cli.main, args=[option, 'test'], catch_exceptions=False)


@pytest.mark.parametrize("verbosity,log_level",
                         [("", logging.WARNING),
                          ("--verbosity=info", logging.INFO),
                          ("--verbosity=debug", logging.DEBUG)])
@mock.patch('planet.cli.cli.logging.basicConfig')
def test_cli_info_verbosity(mock_config, verbosity, log_level):
    """Check that main command configures logging with the proper level."""

    def configtest(stream, level, format):
        assert level == log_level

    mock_config.side_effect = configtest

    # dummy command so we can invoke cli
    @click.command()
    def test():
        pass

    cli.main.add_command(test)

    runner = CliRunner()
    runner.invoke(cli.main, args=[verbosity, 'test'], catch_exceptions=False)


def test_cli_invalid_verbosity():
    """Get a BadParameter error for invalid --verbosity."""

    # dummy command so we can invoke cli
    @click.command()
    def test():
        pass

    cli.main.add_command(test)

    runner = CliRunner()
    result = runner.invoke(cli.main,
                           args=["--verbosity=nothing", 'test'],
                           catch_exceptions=False)
    assert result.exit_code == 2
