# Copyright 2025 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
from contextlib import asynccontextmanager
import json
import click
from planet.cli.io import echo_json
from planet.clients.quota import QuotaClient
from .cmds import command
from .options import compact, limit
from .session import CliSession


@asynccontextmanager
async def quota_client(ctx):
    async with CliSession() as sess:
        cl = QuotaClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Quota API URL.')
def quota(ctx, base_url):
    """Commands for interacting with the Quota API"""
    ctx.obj['BASE_URL'] = base_url


@quota.group()  # type: ignore
def reservations():
    """Commands for managing quota reservations"""
    pass


@command(reservations, name="create")
@click.argument("request_file", type=click.Path(exists=True))
async def reservation_create(ctx, request_file, pretty):
    """Create a new quota reservation from a JSON request file.
    Example:
    \b
    planet quota reservations create ./reservation_request.json
    """
    async with quota_client(ctx) as cl:
        with open(request_file) as f:
            request = json.load(f)
        result = await cl.create_reservation(request)
        echo_json(result, pretty)


@command(reservations, name="list", extra_args=[limit, compact])
@click.option("--status", help="Filter reservations by status")
async def reservations_list(ctx, pretty, limit, compact, status):
    """List quota reservations.
    Example:
    \b
    planet quota reservations list
    planet quota reservations list --status active
    """
    async with quota_client(ctx) as cl:
        results = cl.list_reservations(status=status, limit=limit)
        if compact:
            compact_fields = ('id', 'name', 'status', 'created_at')
            output = [{
                k: v
                for k, v in row.items() if k in compact_fields
            } async for row in results]
        else:
            output = [r async for r in results]
        echo_json(output, pretty)


@command(reservations, name="get")
@click.argument("reservation_id", required=True)
async def reservation_get(ctx, reservation_id, pretty):
    """Get a quota reservation by ID.
    Example:
    \b
    planet quota reservations get 12345678-1234-5678-9012-123456789012
    """
    async with quota_client(ctx) as cl:
        result = await cl.get_reservation(reservation_id)
        echo_json(result, pretty)


@command(reservations, name="cancel")
@click.argument("reservation_id", required=True)
async def reservation_cancel(ctx, reservation_id, pretty):
    """Cancel an existing quota reservation.
    Example:
    \b
    planet quota reservations cancel 12345678-1234-5678-9012-123456789012
    """
    async with quota_client(ctx) as cl:
        result = await cl.cancel_reservation(reservation_id)
        echo_json(result, pretty)


@command(quota, name="estimate")
@click.argument("request_file", type=click.Path(exists=True))
async def quota_estimate(ctx, request_file, pretty):
    """Estimate quota requirements for a potential reservation.
    Example:
    \b
    planet quota estimate ./estimation_request.json
    """
    async with quota_client(ctx) as cl:
        with open(request_file) as f:
            request = json.load(f)
        result = await cl.estimate_quota(request)
        echo_json(result, pretty)


@command(quota, name="usage")
async def quota_usage(ctx, pretty):
    """Get current quota usage and limits.
    Example:
    \b
    planet quota usage
    """
    async with quota_client(ctx) as cl:
        result = await cl.get_quota_usage()
        echo_json(result, pretty)
