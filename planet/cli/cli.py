# Copyright 2017 Planet Labs, PBC.
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
"""CLI main entry point"""
import logging
import sys

import click

import planet
from planet.auth.auth import Auth

from planet.cli import data, orders
from planet.cli.oidcauth import oidc_token_group
from planet.cli.options import \
    opt_auth_client_config_file, \
    opt_auth_profile, \
    opt_token_file

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
@opt_auth_profile
@opt_auth_client_config_file
@opt_token_file
@click.option('--verbosity',
              default="warning",
              help=("Optional: set verbosity level to warning, info, or debug.\
                  Defaults to warning."))
@click.option('--quiet',
              is_flag=True,
              default=False,
              help='Disable ANSI control output.')
@click.version_option(version=planet.__version__)
def main(ctx,
         verbosity,
         quiet,
         auth_profile,
         auth_client_config_file,
         token_file):
    """Planet API Client
    Parameters:
        ctx -- context object
        verbosity -- user input for verbosity."""
    _configure_logging(verbosity)

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)
    ctx.obj['QUIET'] = quiet
    ctx.obj['AUTH'] = Auth.initialize(auth_profile,
                                      auth_client_config_file,
                                      token_file)


def _configure_logging(verbosity):
    """configure logging via verbosity level, corresponding
    to log levels warning, info and debug respectfully.

    Parameters:
        verbosity -- user input for verbosity.
    Raises:
        click.BadParameter: on unexpected parameter input """
    # make the user input string lowercase & strip leading/trailing spaces
    verbosity_input = verbosity.lower()
    verbosity_input = verbosity_input.strip()

    if verbosity_input == 'warning':
        log_level = logging.WARNING
    elif verbosity_input == 'info':
        log_level = logging.INFO
    elif verbosity_input == 'debug':
        log_level = logging.DEBUG
    else:
        raise click.BadParameter("please set verbosity to \
            warning, info, or debug.")
    logging.basicConfig(
        stream=sys.stderr,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


main.add_command(data.data)
main.add_command(orders.orders)
main.add_command(oidc_token_group)

if __name__ == '__main__':
    main()
