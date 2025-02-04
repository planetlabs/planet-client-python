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
"""Quota API CLI"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path

import click

from planet import QuotaClient
from . import types
from .cmds import coro, translate_exceptions
from ..order_request import sentinel_hub
from .io import echo_json
from .options import limit, pretty
from .session import CliSession

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def quota_client(ctx):
    base_url = ctx.obj['BASE_URL']
    async with CliSession() as sess:
        cl = QuotaClient(sess, base_url=base_url)
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Quota API URL.')
def quota(ctx, base_url):
    """Commands for interacting with the Quota API"""
    ctx.ensure_object(dict)
    ctx.obj['BASE_URL'] = base_url or BASE_URL


@quota.command()
@click.pass_context
@coro
async def get_my_products(ctx):
    """Get my products"""
    async with quota_client(ctx) as client:
        products = await client.get_my_products(organization_id=1)
        echo_json(products)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@coro
async def estimate_reservation(ctx, aoi_refs, product_id):
    """Estimate a reservation"""
    async with quota_client(ctx) as client:
        estimate_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id
        }
        estimate = await client.estimate_reservation(estimate_payload)
        echo_json(estimate)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@coro
async def create_reservation(ctx, aoi_refs, product_id):
    """Create a reservation"""
    async with quota_client(ctx) as client:
        create_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id
        }
        created_reservation = await client.create_reservation(create_payload)
        echo_json(created_reservation)


@quota.command()
@click.pass_context
@click.option('--limit', default=10, help='Limit the number of results.')
@coro
async def get_reservations(ctx, limit):
    """Get reservations"""
    async with quota_client(ctx) as client:
        reservations = await client.get_reservations(limit=limit)
        echo_json(reservations)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@coro
async def create_bulk_reservations(ctx, aoi_refs, product_id):
    """Create bulk reservations"""
    async with quota_client(ctx) as client:
        create_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id
        }
        job_details = await client.create_bulk_reservations(create_payload)
        echo_json(job_details)


@quota.command()
@click.pass_context
@click.argument('job_id', type=int)
@coro
async def get_bulk_reservation_job(ctx, job_id):
    """Get bulk reservation job"""
    async with quota_client(ctx) as client:
        job = await client.get_bulk_reservation_job(job_id)
        echo_json(job)
