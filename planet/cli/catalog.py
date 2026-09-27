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
"""Catalog API CLI"""
from contextlib import asynccontextmanager

import click

from planet.cli.io import echo_json
from planet.clients.catalog import CatalogClient

from .cmds import command
from .options import limit
from .session import CliSession
from . import types


@asynccontextmanager
async def catalog_client(ctx):
    async with CliSession(ctx) as sess:
        cl = CatalogClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Catalog API URL (e.g. '
              'https://services-uswest2.sentinel-hub.com/catalog/v1 for the '
              'us-west-2 deployment).')
def catalog(ctx, base_url):
    """Commands for interacting with the Catalog API.

    The Catalog API is a STAC API hosted by Sentinel Hub. It authenticates
    with an OAuth bearer token, so a plain Planet API key will not work - log
    in with an OAuth profile using `planet auth login` first.
    """
    ctx.obj['BASE_URL'] = base_url


@command(catalog, name='landing-page')
async def landing_page(ctx, pretty):
    """Get the Catalog API landing page.

    The landing page is the root STAC Catalog. It lists the conformance
    classes the server implements and links to the collections and search
    endpoints.

    Example:

    planet catalog landing-page --pretty
    """
    async with catalog_client(ctx) as cl:
        result = await cl.get_landing_page()
        echo_json(result, pretty)


@command(catalog, name='conformance')
async def conformance(ctx, pretty):
    """Get the specifications this API conforms to.

    Example:

    planet catalog conformance
    """
    async with catalog_client(ctx) as cl:
        result = await cl.get_conformance()
        echo_json(result, pretty)


@catalog.group()
def collections():
    """Commands for inspecting catalog collections."""
    pass


@command(collections, name='list')
async def collections_list(ctx, pretty):
    """List the collections available to your account.

    Example:

    planet catalog collections list
    """
    async with catalog_client(ctx) as cl:
        results = await cl.list_collections()
        echo_json(results, pretty)


@command(collections, name='get')
@click.argument('collection_id')
async def collection_get(ctx, collection_id, pretty):
    """Describe a single collection.

    Example:

    planet catalog collections get sentinel-2-l2a
    """
    async with catalog_client(ctx) as cl:
        result = await cl.get_collection(collection_id)
        echo_json(result, pretty)


@command(collections, name='queryables')
@click.argument('collection_id')
async def collection_queryables(ctx, collection_id, pretty):
    """Get the properties a collection can be filtered on.

    The returned JSON Schema describes the terms that are valid in the CQL2
    expressions accepted by `--filter`.

    Example:

    planet catalog collections queryables sentinel-2-l2a
    """
    async with catalog_client(ctx) as cl:
        result = await cl.get_collection_queryables(collection_id)
        echo_json(result, pretty)


_bbox_opt = click.option(
    '--bbox',
    type=types.CommaSeparatedFloat(),
    default=None,
    help='Bounding box in CRS84 as west,south,east,north.')

_datetime_opt = click.option(
    '--datetime',
    'datetime_',
    default=None,
    help='RFC 3339 date-time or interval, e.g. '
    '2020-12-10T00:00:00Z/2020-12-30T00:00:00Z. Open intervals use `..`.')

_page_size_opt = click.option('--page-size',
                              type=click.INT,
                              default=100,
                              show_default=True,
                              help='Number of results to fetch per request. '
                              'The API accepts 1-100.')


@catalog.group()
def items():
    """Commands for working with the items in a collection."""
    pass


@command(items, name='list', extra_args=[limit])
@click.argument('collection_id')
@_bbox_opt
@_datetime_opt
@_page_size_opt
async def items_list(ctx,
                     collection_id,
                     bbox,
                     datetime_,
                     limit,
                     page_size,
                     pretty):
    """List the items in a collection.

    Example:

    \b
    planet catalog items list sentinel-2-l2a \\
      --bbox 13,45,14,46 \\
      --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z
    """
    async with catalog_client(ctx) as cl:
        results = cl.list_items(collection_id,
                                bbox=bbox,
                                datetime=datetime_,
                                limit=limit,
                                page_size=page_size)
        async for item in results:
            echo_json(item, pretty)


@command(items, name='get')
@click.argument('collection_id')
@click.argument('item_id')
async def item_get(ctx, collection_id, item_id, pretty):
    """Get a single item from a collection.

    Example:

    \b
    planet catalog items get sentinel-2-l2a \\
      S2B_MSIL2A_20201229T101329_N0214_R022_T33TUK_20201229T115442
    """
    async with catalog_client(ctx) as cl:
        result = await cl.get_item(collection_id, item_id)
        echo_json(result, pretty)


_collections_opt = click.option(
    '--collections',
    type=types.CommaSeparatedString(),
    required=True,
    help='Comma-separated collection IDs to search.')

_search_datetime_opt = click.option(
    '--datetime',
    'datetime_',
    required=True,
    help='RFC 3339 date-time or interval, e.g. '
    '2020-12-10T00:00:00Z/2020-12-30T00:00:00Z. Open intervals use `..`.')

_intersects_opt = click.option(
    '--intersects',
    type=types.JSON(),
    default=None,
    help='GeoJSON geometry to intersect (string, filename, or `-` for stdin).')

_ids_opt = click.option('--ids',
                        type=types.CommaSeparatedString(),
                        default=None,
                        help='Comma-separated item IDs to return.')

_distinct_opt = click.option(
    '--distinct',
    default=None,
    help='Return the unique values of this property instead of full items.')


@command(catalog, name='search', extra_args=[limit])
@_collections_opt
@_search_datetime_opt
@_bbox_opt
@_intersects_opt
@_ids_opt
@click.option('--fields',
              type=types.JSON(),
              default=None,
              help='JSON object with `include` and/or `exclude` lists, e.g. '
              '\'{"include": ["id", "bbox"], "exclude": ["geometry"]}\'.')
@click.option('--filter',
              'filter_',
              default=None,
              help='A CQL2 filter. Text by default (e.g. `eo:cloud_cover>90`);'
              ' pass --filter-lang cql2-json to supply CQL2 JSON.')
@click.option('--filter-lang',
              type=click.Choice(['cql2-text', 'cql2-json']),
              default=None,
              help='The CQL2 encoding used by --filter.')
@click.option('--filter-crs',
              default=None,
              help='CRS used by spatial literals in --filter.')
@_distinct_opt
@_page_size_opt
async def search(ctx,
                 collections,
                 datetime_,
                 bbox,
                 intersects,
                 ids,
                 fields,
                 filter_,
                 filter_lang,
                 filter_crs,
                 distinct,
                 limit,
                 page_size,
                 pretty):
    """Search items with full-featured filtering (POST /search).

    Example:

    \b
    planet catalog search \\
      --collections sentinel-2-l2a \\
      --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \\
      --bbox 13,45,14,46 \\
      --filter 'eo:cloud_cover>90'
    """
    if filter_ is not None and filter_lang == 'cql2-json':
        filter_ = types.JSON().convert(filter_, None, ctx)

    async with catalog_client(ctx) as cl:
        results = cl.search(collections,
                            datetime_,
                            bbox=bbox,
                            intersects=intersects,
                            ids=ids,
                            fields=fields,
                            filter=filter_,
                            filter_lang=filter_lang,
                            filter_crs=filter_crs,
                            distinct=distinct,
                            limit=limit,
                            page_size=page_size)
        async for item in results:
            echo_json(item, pretty)


@command(catalog, name='simple-search', extra_args=[limit])
@_collections_opt
@_search_datetime_opt
@_bbox_opt
@_intersects_opt
@_ids_opt
@click.option('--fields',
              default=None,
              help='Comma-separated attributes to include or exclude, e.g. '
              '`id,type,-geometry,bbox,properties,-links,-assets`.')
@click.option('--filter',
              'filter_',
              default=None,
              help='A CQL2 text filter, e.g. `eo:cloud_cover>90`.')
@_distinct_opt
@_page_size_opt
async def simple_search(ctx,
                        collections,
                        datetime_,
                        bbox,
                        intersects,
                        ids,
                        fields,
                        filter_,
                        distinct,
                        limit,
                        page_size,
                        pretty):
    """Search items with simple filtering (GET /search).

    This is the shorthand search operation: it takes exactly one collection,
    a CQL2 text filter, and a comma-separated fields string. Use
    `planet catalog search` for CQL2 JSON filters or include/exclude fields.

    Example:

    \b
    planet catalog simple-search \\
      --collections sentinel-2-l2a \\
      --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \\
      --bbox 13,45,14,46 \\
      --distinct date
    """
    async with catalog_client(ctx) as cl:
        results = cl.simple_search(collections,
                                   datetime_,
                                   bbox=bbox,
                                   intersects=intersects,
                                   ids=ids,
                                   fields=fields,
                                   filter=filter_,
                                   distinct=distinct,
                                   limit=limit,
                                   page_size=page_size)
        async for item in results:
            echo_json(item, pretty)
