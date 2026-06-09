# Copyright 2026 Planet Labs PBC.
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
"""Quota Reservations CLI"""
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Tuple

import click

from planet.cli.io import echo_json
from planet.clients.quota import QuotaClient

from .cmds import command
from .options import compact, limit
from .session import CliSession
from . import types


@asynccontextmanager
async def quota_client(ctx):
    async with CliSession(ctx) as sess:
        cl = QuotaClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


def _parse_filters(raw: Tuple[str, ...]) -> Optional[Dict[str, str]]:
    """Parse repeated `--filter KEY=VALUE` options into a dict."""
    if not raw:
        return None
    out: Dict[str, str] = {}
    for entry in raw:
        if '=' not in entry:
            raise click.BadParameter(
                f"--filter expects KEY=VALUE; got {entry!r}")
        key, value = entry.split('=', 1)
        key = key.strip()
        if not key:
            raise click.BadParameter(f"--filter has empty key: {entry!r}")
        out[key] = value
    return out


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Account API URL (e.g. '
              'https://api.planet.com/account/v1).')
def quota(ctx, base_url):
    """Commands for interacting with the Quota Reservations API."""
    ctx.obj['BASE_URL'] = base_url


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@quota.group()
def products():
    """Commands for inspecting products that support quota reservations."""
    pass


@command(products, name='list', extra_args=[compact])
@click.option(
    '--supports-reservation/--no-supports-reservation',
    default=None,
    help='Filter products by whether they support quota reservations.')
async def products_list(ctx, supports_reservation, pretty, compact):
    """List products available to your organization.

    Each product's `id` is the value to pass as `--product-id` when creating
    or estimating a reservation.

    Example:

    planet quota products list --supports-reservation
    """
    async with quota_client(ctx) as cl:
        results = await cl.list_products(
            supports_reservation=supports_reservation)
        if compact:
            keys = ('id',
                    'name',
                    'title',
                    'supports_reservation',
                    'quota_total',
                    'quota_used',
                    'unlimited_quota')
            results = [{
                k: v
                for k, v in p.items() if k in keys
            } for p in results]
        echo_json(results, pretty)


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------


@quota.group()
def reservations():
    """Commands for managing quota reservations."""
    pass


@command(reservations, name='list', extra_args=[limit])
@click.option('--fields',
              default=None,
              help='Comma-separated list of fields to include in results.')
@click.option('--sort',
              default=None,
              help='Sort spec, e.g. `created_at` or `-created_at`.')
@click.option('--filter',
              'filters',
              multiple=True,
              metavar='KEY=VALUE',
              help='Filter by `{field}` or `{field}__{op}`. May be repeated.')
@click.option('--page-size',
              type=click.INT,
              default=None,
              help='Number of reservations to return per page.')
async def reservations_list(ctx,
                            pretty,
                            limit,
                            fields,
                            sort,
                            filters,
                            page_size):
    """List quota reservations.

    Example:

    planet quota reservations list --sort -created_at --filter state=active
    """
    async with quota_client(ctx) as cl:
        results = cl.list_reservations(
            limit=limit,
            fields=fields,
            sort=sort,
            filters=_parse_filters(filters),
            page_size=page_size,
        )
        async for item in results:
            echo_json(item, pretty)


@command(reservations, name='get')
@click.argument('reservation_id', type=click.INT)
async def reservation_get(ctx, reservation_id, pretty):
    """Get a single quota reservation by ID.

    Example:

    planet quota reservations get 100
    """
    async with quota_client(ctx) as cl:
        result = await cl.get_reservation(reservation_id)
        echo_json(result, pretty)


def _aoi_refs_from_options(aoi_ref: Tuple[str, ...],
                           aoi_refs_json: Optional[List[str]]) -> List[str]:
    refs: List[str] = list(aoi_ref)
    if aoi_refs_json:
        refs.extend(aoi_refs_json)
    if not refs:
        raise click.BadParameter(
            'At least one AOI ref must be supplied via --aoi-ref or '
            '--aoi-refs.')
    return refs


_aoi_ref_opt = click.option('--aoi-ref',
                            multiple=True,
                            metavar='REF',
                            help='An AOI feature reference. May be repeated. '
                            'Example: pl:features/my/my-collection/feature-id')

_aoi_refs_json_opt = click.option(
    '--aoi-refs',
    'aoi_refs_json',
    type=types.JSON(),
    default=None,
    help='JSON array of AOI feature refs (string, filename, or `-` for stdin).'
)

_product_id_opt = click.option('--product-id',
                               type=click.INT,
                               required=True,
                               help='Product ID from `/my/products`.')

_collection_id_opt = click.option(
    '--collection-id',
    default=None,
    help='Optional grouping collection for the reservation.')


@command(reservations, name='create')
@_aoi_ref_opt
@_aoi_refs_json_opt
@_product_id_opt
@_collection_id_opt
async def reservation_create(ctx,
                             aoi_ref,
                             aoi_refs_json,
                             product_id,
                             collection_id,
                             pretty):
    """Create one or more quota reservations.

    Example:

    \b
    planet quota reservations create \\
      --aoi-ref pl:features/my/my-collection/feature-id \\
      --product-id 123
    """
    refs = _aoi_refs_from_options(aoi_ref, aoi_refs_json)
    async with quota_client(ctx) as cl:
        result = await cl.create_reservation(refs, product_id, collection_id)
        echo_json(result, pretty)


@command(reservations, name='bulk-reserve')
@_aoi_ref_opt
@_aoi_refs_json_opt
@_product_id_opt
@_collection_id_opt
async def reservation_bulk_reserve(ctx,
                                   aoi_ref,
                                   aoi_refs_json,
                                   product_id,
                                   collection_id,
                                   pretty):
    """Submit a bulk quota reservation job (asynchronous).

    Returns a payload with `job_id` and `status`. Track progress with
    `planet quota jobs get JOB_ID`.
    """
    refs = _aoi_refs_from_options(aoi_ref, aoi_refs_json)
    async with quota_client(ctx) as cl:
        result = await cl.bulk_create_reservations(refs,
                                                   product_id,
                                                   collection_id)
        echo_json(result, pretty)


@command(reservations, name='estimate')
@_aoi_ref_opt
@_aoi_refs_json_opt
@_product_id_opt
@_collection_id_opt
async def reservation_estimate(ctx,
                               aoi_ref,
                               aoi_refs_json,
                               product_id,
                               collection_id,
                               pretty):
    """Estimate the quota cost of a reservation without creating it."""
    refs = _aoi_refs_from_options(aoi_ref, aoi_refs_json)
    async with quota_client(ctx) as cl:
        result = await cl.estimate_reservation(refs, product_id, collection_id)
        echo_json(result, pretty)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@quota.group()
def jobs():
    """Commands for tracking bulk quota reservation jobs."""
    pass


@command(jobs, name='list', extra_args=[limit])
@click.option('--fields',
              default=None,
              help='Comma-separated list of fields to include in results.')
@click.option('--sort', default=None, help='Sort spec, e.g. `id` or `-id`.')
@click.option('--filter',
              'filters',
              multiple=True,
              metavar='KEY=VALUE',
              help='Filter by `{field}` or `{field}__{op}`. May be repeated.')
@click.option('--page-size',
              type=click.INT,
              default=None,
              help='Number of jobs to return per page.')
async def jobs_list(ctx, pretty, limit, fields, sort, filters, page_size):
    """List bulk quota reservation jobs."""
    async with quota_client(ctx) as cl:
        results = cl.list_jobs(
            limit=limit,
            fields=fields,
            sort=sort,
            filters=_parse_filters(filters),
            page_size=page_size,
        )
        async for item in results:
            echo_json(item, pretty)


@command(jobs, name='get')
@click.argument('job_id')
async def job_get(ctx, job_id, pretty):
    """Get the status of a bulk reservation job.

    Example:

    planet quota jobs get 7b7e3a3a-...
    """
    async with quota_client(ctx) as cl:
        result = await cl.get_job(job_id)
        echo_json(result, pretty)
