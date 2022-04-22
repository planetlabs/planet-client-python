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

from planet.cli import orders
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
@click.option('-v',
              '--verbose',
              count=True,
              help=('Specify verbosity level of between 0 and 2 corresponding '
                    'to log levels warning, info, and debug respectively.'))
@click.version_option(version=planet.__version__)
def main(ctx, verbose, auth_profile, auth_client_config_file, token_file):
    '''Planet API Client'''
    _configure_logging(verbose)

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    auth = Auth.initialize(auth_profile, auth_client_config_file, token_file)
    ctx.obj['AUTH'] = auth
    ctx.obj['AUTH_PROFILE'] = auth_profile
    ctx.obj['AUTH_CLIENT'] = auth.auth_client()
    ctx.obj['AUTH_REQUEST_AUTHENTICATOR'] = auth.request_authenticator()
    ctx.obj['AUTH_TOKEN_FILE_PATH'] = auth.token_file_path()


def _configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG * verbosity)
    logging.basicConfig(
        stream=sys.stderr,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


main.add_command(orders.orders)
main.add_command(oidc_token_group)

if __name__ == '__main__':
    main()
