# Copyright 2017 Planet Labs, Inc.
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

from .auth import auth
from .orders import orders


LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('--verbosity',
              type=click.Choice(['warning', 'info', 'debug', 'none']),
              help='Set maximum log level.')
@click.option('--quiet',
              is_flag=True, default=False,
              help='Disable all progress reporting.')
@click.version_option(version=planet.__version__)
def main(ctx, verbosity, quiet):
    """Planet API SDK Command Line Interface"""
    _configure_logging(verbosity)

    ctx.ensure_object(dict)
    # TODO: store quiet flag


def _configure_logging(verbosity):
    """set logging level from verbosity parameter"""
    # TODO: get log_level from verbosity
    log_level = logging.DEBUG
    # log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)

    logging.basicConfig(
        stream=sys.stderr, level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


main.add_command(auth)
main.add_command(orders)
