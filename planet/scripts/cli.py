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
import asyncio
from functools import wraps
import json
import logging
import sys

import click

import planet


# https://github.com/pallets/click/issues/85#issuecomment-503464628
def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@click.group()
@click.pass_context
@click.option('-v', '--verbose', count=True,
              help=('Specify verbosity level of between 0 and 2 corresponding '
                    'to log levels warning, info, and debug respectively.'))
@click.version_option(version=planet.__version__)
def cli(ctx, verbose):
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
@click.password_option('--password', confirmation_prompt=False, help=(
    'Account password. Will not be saved.'
))
def init(ctx, email, password):
    '''Obtain and store authentication information'''
    base_url = ctx.obj["BASE_URL"]
    auth = planet.Auth.from_login(email, password, base_url=base_url)
    auth.write()
    click.echo('Initialized')


@auth.command()
def value():
    '''Print the stored authentication information'''
    try:
        auth = planet.Auth.from_file()
        click.echo(auth.value)
    except planet.auth.AuthException:
        click.echo(
            'Stored authentication information cannot be found. '
            'Please store authentication information with `planet auth init`.')


@cli.group()
@click.pass_context
@click.option('-u', '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def orders(ctx, base_url):
    '''Commands for interacting with the Orders API'''
    auth = planet.Auth.read()
    ctx.obj['AUTH'] = auth
    ctx.obj['BASE_URL'] = base_url


@orders.command()
@click.pass_context
@coro
@click.option('--state',
              help='Filter orders to given state.',
              type=click.Choice(planet.api.orders.ORDERS_STATES,
                                case_sensitive=False))
@click.option('--limit', help='Filter orders to given limit.',
              default=None, type=int)
async def list(ctx, state, limit):
    '''List orders'''
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']

    async with planet.Session(auth=auth) as sess:
        cl = planet.OrdersClient(sess, base_url=base_url)
        orders = await cl.list_orders(state=state, limit=limit, as_json=True)

    click.echo(json.dumps(orders))
