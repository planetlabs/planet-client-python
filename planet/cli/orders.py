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
"""Orders API CLI"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path

import click

import planet
from planet import OrdersClient  # allow mocking
from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def orders_client(ctx):
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']
    async with CliSession(auth=auth) as sess:
        cl = OrdersClient(sess, base_url=base_url)
        yield cl


@click.group()
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def orders(ctx, base_url):
    '''Commands for interacting with the Orders API'''
    ctx.obj['AUTH'] = None
    ctx.obj['BASE_URL'] = base_url


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.option('--state',
              help='Filter orders to given state.',
              type=click.Choice(planet.clients.orders.ORDER_STATE_SEQUENCE,
                                case_sensitive=False))
@limit
@pretty
async def list(ctx, state, limit, pretty):
    '''List orders

    This command prints a sequence of the returned order descriptions,
    optionally pretty-printed.
    '''
    async with orders_client(ctx) as cl:
        orders = await cl.list_orders(state=state, limit=limit)
        async for o in orders:
            echo_json(o, pretty)


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

    echo_json(order, pretty)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
async def cancel(ctx, order_id):
    '''Cancel order by order ID.

    This command cancels a queued order and outputs the cancelled order
    details.
    '''
    async with orders_client(ctx) as cl:
        json_resp = await cl.cancel_order(str(order_id))

    click.echo(json_resp)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@click.option('--delay',
              type=int,
              default=5,
              help='Time (in seconds) between polls.')
@click.option('--max-attempts',
              type=int,
              default=200,
              show_default=True,
              help='Maximum number of polls. Set to zero for no limit.')
@click.option('--state',
              help='State prior to a final state that will end polling.',
              type=click.Choice(planet.clients.orders.ORDER_STATE_SEQUENCE,
                                case_sensitive=False))
async def wait(ctx, order_id, delay, max_attempts, state):
    """Wait until order reaches desired state.

    Reports the state of the order on the last poll.

    This function polls the Orders API to determine the order state, with
    the specified delay between each polling attempt, until the
    order reaches a final state or earlier state, if specified.
    If the maximum number of attempts is reached before polling is
    complete, an exception is raised. Setting --max-attempts to zero will
    result in no limit on the number of attempts.

    Setting --delay to zero results in no delay between polling attempts.
    This will likely result in throttling by the Orders API, which has
    a rate limit of 10 requests per second. If many orders are being
    polled asynchronously, consider increasing the delay to avoid
    throttling.

    By default, polling completes when the order reaches a final state.
    If --state is specified, polling will complete when the specified earlier
    state is reached or passed.
    """
    quiet = ctx.obj['QUIET']
    async with orders_client(ctx) as cl:
        with planet.reporting.StateBar(order_id=order_id,
                                       disable=quiet) as bar:
            state = await cl.wait(str(order_id),
                                  state=state,
                                  delay=delay,
                                  max_attempts=max_attempts,
                                  callback=bar.update_state)
    click.echo(state)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@click.option('--checksum',
              default=None,
              type=click.Choice(['MD5', 'SHA256'], case_sensitive=False),
              help=('Verify that checksums match.'))
@click.option('--directory',
              default='.',
              help=('Base directory for file download.'),
              type=click.Path(exists=True,
                              resolve_path=True,
                              writable=True,
                              file_okay=False))
@click.option('--overwrite',
              is_flag=True,
              default=False,
              help=('Overwrite files if they already exist.'))
async def download(ctx, order_id, overwrite, directory, checksum):
    """Download order by order ID.

    If --checksum is provided, the associated checksums given in the manifest
    are compared against the downloaded files to verify that they match.

    If --checksum is provided, files are already downloaded, and --overwrite is
    not specified, this will simply validate the checksums of the files against
    the manifest.
    """
    quiet = ctx.obj['QUIET']
    async with orders_client(ctx) as cl:
        await cl.download_order(
            str(order_id),
            directory=Path(directory),
            overwrite=overwrite,
            progress_bar=not quiet,
        )
        if checksum:
            cl.validate_checksum(Path(directory, str(order_id)), checksum)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument("request", type=types.JSON(), default="-", required=False)
@pretty
async def create(ctx, request: str, pretty):
    '''Create an order.

    This command outputs the created order description, optionally
    pretty-printed.

    REQUEST is the full description of the order to be created. It must be JSON
    and can be specified a json string, filename, or '-' for stdin.
    '''
    async with orders_client(ctx) as cl:
        order = await cl.create_order(request)

    echo_json(order, pretty)


@orders.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('item_type',
                metavar='ITEM_TYPE',
                type=click.Choice(planet.specs.get_item_types(),
                                  case_sensitive=False))
@click.argument('bundle',
                metavar='BUNDLE',
                type=click.Choice(planet.specs.get_product_bundles(),
                                  case_sensitive=False))
@click.option('--name',
              required=True,
              help='Order name. Does not need to be unique.',
              type=click.STRING)
@click.option('--id',
              help='One or more comma-separated item IDs.',
              type=types.CommaSeparatedString(),
              required=True)
@click.option('--clip',
              type=types.JSON(),
              help="""Clip feature GeoJSON. Can be a json string, filename,
              or '-' for stdin.""")
@click.option(
    '--tools',
    type=types.JSON(),
    help="""Toolchain JSON. Can be a json string, filename, or '-' for
    stdin.""")
@click.option('--email',
              default=False,
              is_flag=True,
              help='Send email notification when order is complete.')
@click.option(
    '--cloudconfig',
    type=types.JSON(),
    help="""Credentials for cloud storage provider to enable cloud delivery of
    data. Can be a json string, filename, or '-' for stdin.""")
@click.option(
    '--stac/--no-stac',
    default=True,
    is_flag=True,
    help="""Include or exclude metadata in SpatioTemporal Asset Catalog (STAC)
    format. Not specifying either defaults to including it (--stac).""")
@pretty
async def request(ctx,
                  item_type,
                  bundle,
                  name,
                  id,
                  clip,
                  tools,
                  email,
                  cloudconfig,
                  stac,
                  pretty):
    """Generate an order request.

    This command provides support for building an order description used
    in creating an order. It outputs the order request, optionally pretty-
    printed.
    """
    try:
        product = planet.order_request.product(id, bundle, item_type)
    except planet.specs.SpecificationException as e:
        raise click.BadParameter(e)

    if email:
        notifications = planet.order_request.notifications(email=email)
    else:
        notifications = None

    if clip and tools:
        raise click.BadParameter("Specify only one of '--clip' or '--tools'")
    elif clip:
        try:
            clip = planet.geojson.as_polygon(clip)
        except planet.exceptions.GeoJSONError as e:
            raise click.BadParameter(e)

        tools = [planet.order_request.clip_tool(clip)]

    if cloudconfig:
        delivery = planet.order_request.delivery(cloud_config=cloudconfig)
    else:
        delivery = None

    if stac:
        stac_json = {'stac': {}}
    else:
        stac_json = {}

    request = planet.order_request.build_request(name,
                                                 products=[product],
                                                 delivery=delivery,
                                                 notifications=notifications,
                                                 tools=tools,
                                                 stac=stac_json)

    echo_json(request, pretty)
