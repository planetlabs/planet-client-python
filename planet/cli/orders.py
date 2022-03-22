# Copyright 2022 Planet Labs, PBC.
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
"""Orders API CLI"""
from contextlib import asynccontextmanager
import json
import logging

import click

import planet
from planet import OrdersClient, Session  # allow mocking

from .cmds import coro, translate_exceptions
from .io import echo_json

LOGGER = logging.getLogger(__name__)

pretty = click.option('--pretty', is_flag=True, help='Format JSON output')


@asynccontextmanager
async def orders_client(ctx):
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']
    async with Session(auth=auth) as sess:
        cl = OrdersClient(sess, base_url=base_url)
        yield cl


@click.group()
@click.pass_context
@click.option('-u', '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def orders(ctx, base_url):
    '''Commands for interacting with the Orders API'''
    ctx.obj['AUTH'] = planet.Auth.from_file()
    ctx.obj['BASE_URL'] = base_url


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.option('-s', '--state',
              help='Filter orders to given state.',
              type=click.Choice(planet.clients.orders.ORDERS_STATES,
                                case_sensitive=False))
@click.option('-l', '--limit', help='Filter orders to given limit.',
              default=None, type=int)
@pretty
async def list(ctx, state, limit, pretty):
    '''List orders'''
    async with orders_client(ctx) as cl:
        orders = await cl.list_orders(state=state, limit=limit, as_json=True)

    echo_json(orders, pretty)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@pretty
async def get(ctx, order_id, pretty):
    """Get order

    This command outputs the order description, optionally pretty-printed.
    """
    async with orders_client(ctx) as cl:
        order = await cl.get_order(str(order_id))

    echo_json(order.json, pretty)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
async def cancel(ctx, order_id):
    '''Cancel order by order ID.'''
    async with orders_client(ctx) as cl:
        await cl.cancel_order(str(order_id))

    click.echo('Cancelled')


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@click.option('-q', '--quiet', is_flag=True, default=False,
              help=('Disable ANSI control output.'))
@click.option('-o', '--overwrite', is_flag=True, default=False,
              help=('Overwrite files if they already exist.'))
@click.option('--dest', default='.',
              help=('Directory to download files to.'),
              type=click.Path(exists=True, resolve_path=True,
                              writable=True, file_okay=False))
async def download(ctx, order_id, quiet, overwrite, dest):
    '''Download order by order ID.'''

    # Download the user's order
    async with orders_client(ctx) as cl:
        with planet.reporting.StateBar(order_id=order_id,
                                       disable=quiet) as bar:
            await cl.poll(str(order_id), report=bar.update)
            _ = await cl.download_order(
                    str(order_id),
                    directory=dest,
                    overwrite=overwrite,
                    progress_bar=not quiet)


def split_id_list(ctx, param, value):
    # split list by ',' and remove whitespace
    ids = [i.strip() for i in value.split(',')]

    # validate passed ids
    for iid in ids:
        if not iid:
            raise click.BadParameter('id cannot be empty string.')

    return ids


def read_file_geojson(ctx, param, value):
    # skip this if the filename is None
    if not value:
        return value

    json_value = read_file_json(ctx, param, value)
    geo = planet.geojson.as_geom(json_value)
    return geo


def read_file_json(ctx, param, value):
    # skip this if the filename is None
    if not value:
        return value

    try:
        LOGGER.debug('reading json from file')
        json_value = json.load(value)
    except json.decoder.JSONDecodeError:
        raise click.ClickException('File does not contain valid json.')

    return json_value


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.option('--name', required=True)
@click.option('--id', 'ids', help='One or more comma-separated item IDs',
              type=click.STRING, callback=split_id_list, required=True)
# @click.option('--ids_from_search',
#               help='Embedded data search')
@click.option('--bundle', multiple=False, required=True,
              help='Specify bundle',
              type=click.Choice(planet.specs.get_product_bundles(),
                                case_sensitive=False),
              )
@click.option('--item-type', multiple=False, required=True,
              help='Specify an item type',
              type=click.STRING)
@click.option('--email', default=False, is_flag=True,
              help='Send email notification when Order is complete')
@click.option('--cloudconfig', help='Cloud delivery config json file.',
              type=click.File('rb'), callback=read_file_json)
@click.option('--clip', help='Clip GeoJSON file.',
              type=click.File('rb'), callback=read_file_geojson)
@click.option('--tools', help='Toolchain json file.',
              type=click.File('rb'), callback=read_file_json)
@pretty
async def create(ctx, name, ids, bundle, item_type, email, cloudconfig, clip,
                 tools, pretty):
    '''Create an order.'''
    try:
        product = planet.order_request.product(ids, bundle, item_type)
    except planet.specs.SpecificationException as e:
        raise click.BadParameter(e)

    if email:
        notifications = planet.order_request.notifications(email=email)
    else:
        notifications = None

    if cloudconfig:
        delivery = planet.order_request.delivery(
            cloud_config=cloudconfig
        )
    else:
        delivery = None

    if clip and tools:
        raise click.BadParameter("Specify only one of '--clip' or '--tools'")
    elif clip:
        try:
            clip = planet.geojson.as_polygon(clip)
        except planet.geojson.GeoJSONException as e:
            raise click.BadParameter(e)

        tools = [planet.order_request.clip_tool(clip)]

    request = planet.order_request.build_request(
        name,
        products=[product],
        delivery=delivery,
        notifications=notifications,
        tools=tools)

    async with orders_client(ctx) as cl:
        order = await cl.create_order(request)

    echo_json(order.json, pretty)
