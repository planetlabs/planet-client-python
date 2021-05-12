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

import click
import logging
import sys

import planet
# from planet import __version__
from planet.constants import PLANET_BASE_URL


@click.group()
@click.pass_context
@click.option('-v', '--verbose', count=True,
              help=('Specify verbosity level of between 0 and 2 corresponding '
                    'to log levels warning, info, and debug respectively.'))
@click.option('-u', '--base-url',
              default=PLANET_BASE_URL, show_default=True,
              help='Change base Planet API URL.')
@click.version_option(version=planet.__version__)
def cli(ctx, verbose, base_url):
    '''Planet API Client'''
    _configure_logging(verbose)

    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)
    # ctx.obj['BASE_URL'] = base_url


def _configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)
    logging.basicConfig(
        stream=sys.stderr, level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@cli.group()
@click.pass_context
@click.option('-u', '--base-url',
              default=None,
              help='Assign custom base Auth API URL.')
def auth(ctx, base_url):
    '''Commands for working with Planet authentication'''
    ctx.obj['BASE_URL'] = base_url


@auth.command()
@click.pass_context
@click.option('--email', default=None, prompt=True, help=(
    'The email address associated with your Planet credentials.'
))
@click.password_option('--password', help=(
    'Account password. Will not be saved.'
))
def init(ctx, email, password):
    '''Login using email/password'''
    # auth = planet.Auth.from_login(email, pw)
    click.echo(f'base_url: {ctx.obj["BASE_URL"]}')

# @cli.group('orders')
# def orders():
#     '''Commands for interacting with the Orders API'''
#     pass
#
#
# @orders.command('list')
# # @click.option('--status', help="'all', 'in-progress', 'completed'")
# @pretty
# def list_orders(pretty):
#     '''List all pending order requests; optionally filter by status'''
#     cl = clientv1()
#     echo_json_response(call_and_wrap(cl.get_orders), pretty)
