# Copyright 2025 Planet Labs PBC.
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
"""Tasking API CLI"""
from contextlib import asynccontextmanager
import json
import logging

import click

from planet import TaskingClient
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession
from .validators import check_geom

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def tasking_client(ctx):
    base_url = ctx.obj['BASE_URL']
    async with CliSession(ctx) as sess:
        cl = TaskingClient(sess, base_url=base_url)
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Tasking API URL.')
def tasking(ctx, base_url):
    """Commands for interacting with the Tasking API"""
    ctx.obj['BASE_URL'] = base_url


@tasking.command('create-order')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.option('--request',
              type=click.File(),
              help='Request specification as a JSON file.')
@click.option('--name', help='Name for the tasking order.')
@click.option('--geometry',
              callback=check_geom,
              help='Geometry as GeoJSON string or @file.geojson.')
@pretty
async def create_order(ctx, request, name, geometry, pretty):
    """Create a tasking order.

    Example:
        planet tasking create-order --request order.json
        planet tasking create-order --name "my order" --geometry '{"type":"Point","coordinates":[-122,37]}'
    """
    if request:
        request_data = json.load(request)
    elif name and geometry:
        request_data = {
            'name': name,
            'geometry': geometry,
            'products': [{
                'item_type': 'skysat_collect', 'asset_type': 'ortho_analytic'
            }]
        }
    else:
        raise click.UsageError(
            'Either --request file or --name and --geometry must be provided')

    async with tasking_client(ctx) as client:
        order = await client.create_order(request_data)
        echo_json(order, pretty)


@tasking.command('get-order')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id')
@pretty
async def get_order(ctx, order_id, pretty):
    """Get a tasking order by ID."""
    async with tasking_client(ctx) as client:
        order = await client.get_order(order_id)
        echo_json(order, pretty)


@tasking.command('cancel-order')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id')
@pretty
async def cancel_order(ctx, order_id, pretty):
    """Cancel a tasking order."""
    async with tasking_client(ctx) as client:
        order = await client.cancel_order(order_id)
        echo_json(order, pretty)


@tasking.command('list-orders')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.option(
    '--state',
    help='Filter by order state (queued, running, success, failed, cancelled).'
)
@limit
@pretty
async def list_orders(ctx, state, limit, pretty):
    """List tasking orders."""
    async with tasking_client(ctx) as client:
        async for order in client.list_orders(state=state, limit=limit):
            echo_json(order, pretty)


@tasking.command('wait-order')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id')
@click.option('--state',
              default='success',
              help='State to wait for (default: success).')
@click.option('--delay',
              type=int,
              default=5,
              help='Delay between polling attempts in seconds (default: 5).')
@click.option('--max-attempts',
              type=int,
              default=200,
              help='Maximum number of polling attempts (default: 200).')
@pretty
async def wait_order(ctx, order_id, state, delay, max_attempts, pretty):
    """Wait for a tasking order to reach a specified state."""

    def callback(order):
        """Print order status during polling."""
        echo_json({'order_id': order['id'], 'state': order['state']}, pretty)

    async with tasking_client(ctx) as client:
        await client.wait_order(order_id=order_id,
                                state=state,
                                delay=delay,
                                max_attempts=max_attempts,
                                callback=callback)

        # Get final order details
        final_order = await client.get_order(order_id)
        echo_json(final_order, pretty)


@tasking.command('get-results')  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id')
@pretty
async def get_results(ctx, order_id, pretty):
    """Get results for a completed tasking order."""
    async with tasking_client(ctx) as client:
        results = await client.get_order_results(order_id)
        echo_json({'results': results}, pretty)
