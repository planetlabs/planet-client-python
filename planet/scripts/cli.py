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


pretty = click.option('-pp', '--pretty', is_flag=True,
                      help='Format JSON output')


def pprint(json_dict):
    return json.dumps(json_dict, indent=2, sort_keys=True)


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
@click.option('-s', '--state',
              help='Filter orders to given state.',
              type=click.Choice(planet.api.orders.ORDERS_STATES,
                                case_sensitive=False))
@click.option('-l', '--limit', help='Filter orders to given limit.',
              default=None, type=int)
@pretty
async def list(ctx, state, limit, pretty):
    '''List orders'''
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']

    async with planet.Session(auth=auth) as sess:
        cl = planet.OrdersClient(sess, base_url=base_url)
        orders = await cl.list_orders(state=state, limit=limit, as_json=True)

    if pretty:
        click.echo(pprint(orders))
    else:
        click.echo(orders)


@orders.command()
@click.pass_context
@coro
@click.argument('order_id', type=click.UUID)
@pretty
async def get(ctx, order_id, pretty):
    '''Get order by order id.'''
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']

    async with planet.Session(auth=auth) as sess:
        cl = planet.OrdersClient(sess, base_url=base_url)
        order = await cl.get_order(str(order_id))

    if pretty:
        click.echo(pprint(order.json))
    else:
        click.echo(order.json)


@orders.command()
@click.pass_context
@coro
@click.argument('order_id', type=click.UUID)
async def cancel(ctx, order_id):
    '''Get order by order id.'''
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']

    async with planet.Session(auth=auth) as sess:
        cl = planet.OrdersClient(sess, base_url=base_url)
        await cl.cancel_order(str(order_id))

    click.echo('Cancelled')
#
# @orders.command()
# @click.pass_context
# @coro
# @click.option('--name', required=True)
# @click.option('--id', help='One or more comma-separated item IDs',
#               cls=RequiredUnless, this_opt_exists='ids_from_search')
# # Note: This is passed as a string, because --item-type is a required field for
# # both 'data search' and 'orders create'.
# @click.option('--ids_from_search',
#               help='Embedded data search')
# @click.option('--clip', type=ClipAOI(),
#               help='Provide a GeoJSON AOI Geometry for clipping')
# @click.option('--email', default=False, is_flag=True,
#               help='Send email notification when Order is complete')
# @click.option('--cloudconfig', help=('Path to cloud delivery config'),
#               type=click.Path(exists=True, resolve_path=True, readable=True,
#                               allow_dash=False, dir_okay=False,
#                               file_okay=True))
# @click.option('--tools', help=('Path to toolchain json'),
#               type=click.Path(exists=True, resolve_path=True, readable=True,
#                               allow_dash=False, dir_okay=False,
#                               file_okay=True))
# @bundle_option
# @click.option(
#     '--item-type', multiple=False, required=True, type=ItemType(), help=(
#         'Specify an item type'
#     )
# )
# @orders.command()
# @pretty
# def create(**kwargs):
#     '''Create an order'''
#     ids_from_search = kwargs.get('ids_from_search')
#     if ids_from_search is not None:
#         runner = CliRunner()
#         resp = runner.invoke(quick_search, ids_from_search).output
#         try:
#             id_list = ids_from_search_response(resp)
#         except ValueError:
#             raise click.ClickException('ids_from_search, {}'.format(resp))
#         kwargs['id'] = id_list
#         del kwargs['ids_from_search']
#     cl = clientv1()
#     request = create_order_request(**kwargs)
#     echo_json_response(call_and_wrap(cl.create_order, request), pretty)
