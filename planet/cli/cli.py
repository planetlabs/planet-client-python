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
import logging
import sys

import click

import planet

from . import auth, orders

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('-v', '--verbose', count=True,
              help=('Specify verbosity level of between 0 and 2 corresponding '
                    'to log levels warning, info, and debug respectively.'))
@click.version_option(version=planet.__version__)
def main(ctx, verbose):
    '''Planet API Client'''
    _configure_logging(verbose)

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)


def _configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)
    logging.basicConfig(
        stream=sys.stderr, level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


main.add_command(auth.auth)
main.add_command(orders.orders)
