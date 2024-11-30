# Copyright 2017 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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

import planet_auth_utils
import planet

from . import cmds, collect, data, orders, subscriptions

LOGGER = logging.getLogger(__name__)


@click.group()  # type: ignore
@click.pass_context
@click.option('--quiet',
              is_flag=True,
              default=False,
              help='Disable ANSI control output.')
@click.version_option(version=planet.__version__)
@click.option('--verbosity',
              default="warning",
              help=("Optional: set verbosity level to warning, info, or debug.\
                  Defaults to warning."))
@planet_auth_utils.opt_auth_profile
@planet_auth_utils.opt_auth_client_id
@planet_auth_utils.opt_auth_client_secret
@planet_auth_utils.opt_auth_api_key
@cmds.translate_exceptions
def main(ctx, verbosity, quiet, auth_profile, auth_client_id, auth_client_secret, auth_api_key):
    """Planet SDK for Python CLI"""
    _configure_logging(verbosity)

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)
    ctx.obj['QUIET'] = quiet

    _configure_cli_auth_ctx(ctx, auth_profile, auth_client_id, auth_client_secret, auth_api_key)


def _configure_cli_auth_ctx(ctx, auth_profile, auth_client_id, auth_client_secret, auth_api_key):
    # planet-auth library Auth context type
    ctx.obj['AUTH'] = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
        auth_profile_opt=auth_profile,
        auth_client_id_opt=auth_client_id,
        auth_client_secret_opt=auth_client_secret,
        auth_api_key_opt=auth_api_key,
    )

    # planet SDK Auth context type
    ctx.obj['PLSDK_AUTH'] = planet.Auth.from_plauth(pl_authlib_context=ctx.obj['AUTH'])


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


main.add_command(cmd=planet_auth_utils.embedded_plauth_cmd_group, name="auth")  # type: ignore
main.add_command(data.data)  # type: ignore
main.add_command(orders.orders)  # type: ignore
main.add_command(subscriptions.subscriptions)  # type: ignore
main.add_command(collect.collect)  # type: ignore
