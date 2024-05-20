# Copyright 2022 Planet Labs PBC.
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
"""The Planet Data CLI."""
from typing import List, Optional
from contextlib import asynccontextmanager
from pathlib import Path
import click

from planet.reporting import AssetStatusBar
from planet import data_filter, DataClient, exceptions
from planet.clients.data import (SEARCH_SORT,
                                 LIST_SEARCH_TYPE,
                                 LIST_SEARCH_TYPE_DEFAULT,
                                 LIST_SORT_ORDER,
                                 LIST_SORT_DEFAULT,
                                 SEARCH_SORT_DEFAULT,
                                 STATS_INTERVAL)

from planet.specs import (get_data_item_types,
                          validate_data_item_type,
                          SpecificationException)

from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession
from .validators import check_geom

valid_item_string = "Valid entries for ITEM_TYPES: " + "|".join(
    get_data_item_types())


@asynccontextmanager
async def data_client(ctx):
    async with CliSession() as sess:
        cl = DataClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def data(ctx, base_url):
    """Commands for interacting with the Data API"""
    ctx.obj['BASE_URL'] = base_url


# TODO: filter().
def geom_to_filter(ctx, param, value: Optional[dict]) -> Optional[dict]:
    return data_filter.geometry_filter(value) if value else None


def assets_to_filter(ctx, param, assets: List[str]) -> Optional[dict]:
    # TODO: validate and normalize
    return data_filter.asset_filter(assets) if assets else None


def check_item_types(ctx, param, item_types) -> Optional[List[dict]]:
    """Validates each item types provided by comparing them to all supported
    item types."""
    try:
        for item_type in item_types:
            validate_data_item_type(item_type)
        return item_types
    except SpecificationException as e:
        raise click.BadParameter(str(e))


def check_item_type(ctx, param, item_type) -> Optional[List[dict]]:
    """Validates the item type provided by comparing it to all supported
    item types."""
    try:
        validate_data_item_type(item_type)
    except SpecificationException as e:
        raise click.BadParameter(str(e))

    return item_type


def check_search_id(ctx, param, search_id) -> str:
    """Ensure search id is a valix hex string"""
    try:
        _ = DataClient._check_search_id(search_id)
    except exceptions.ClientError as e:
        raise click.BadParameter(str(e))
    return search_id


def date_range_to_filter(ctx, param, values) -> Optional[List[dict]]:

    def _func(obj):
        field, comp, value = obj
        kwargs = {'field_name': field, comp: value}
        return data_filter.date_range_filter(**kwargs)

    return [_func(v) for v in values] if values else None


def range_to_filter(ctx, param, values) -> Optional[List[dict]]:

    def _func(obj):
        field, comp, value = obj
        kwargs = {'field_name': field, comp: value}
        return data_filter.range_filter(**kwargs)

    return [_func(v) for v in values] if values else None


def update_to_filter(ctx, param, values) -> Optional[List[dict]]:

    def _func(obj):
        field, comp, value = obj
        kwargs = {'field_name': field, comp: value}
        return data_filter.update_filter(**kwargs)

    return [_func(v) for v in values] if values else None


def number_in_to_filter(ctx, param, values) -> Optional[List[dict]]:

    def _func(obj):
        field, values = obj
        return data_filter.number_in_filter(field_name=field, values=values)

    return [_func(v) for v in values] if values else None


def string_in_to_filter(ctx, param, values) -> Optional[List[dict]]:

    def _func(obj):
        field, values = obj
        return data_filter.string_in_filter(field_name=field, values=values)

    return [_func(v) for v in values] if values else None


@data.command()  # type: ignore
@click.pass_context
@translate_exceptions
@click.option('--asset',
              type=types.CommaSeparatedString(),
              default=None,
              callback=assets_to_filter,
              help="""Filter to items with one or more of specified assets.
    TEXT is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option('--date-range',
              type=click.Tuple(
                  [types.Field(), types.Comparison(), types.DateTime()]),
              callback=date_range_to_filter,
              multiple=True,
              help="""Filter by date range in field.
    FIELD is the name of the field to filter on.
    COMP can be lt, lte, gt, or gte.
    DATETIME can be an RFC3339 or ISO 8601 string.""")
@click.option('--geom',
              type=types.JSON(),
              callback=geom_to_filter,
              help="""Filter to items that overlap a given geometry. Can be a
              json string, filename, or '-' for stdin.""")
@click.option('--number-in',
              type=click.Tuple([types.Field(), types.CommaSeparatedFloat()]),
              multiple=True,
              callback=number_in_to_filter,
              help="""Filter field by numeric in.
    FIELD is the name of the field to filter on.
    VALUE is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option('--permission',
              is_flag=True,
              default=False,
              show_default=True,
              help='Filter to assets with download permissions.')
@click.option('--range',
              'nrange',
              type=click.Tuple([types.Field(), types.Comparison(), float]),
              callback=range_to_filter,
              multiple=True,
              help="""Filter by number range in field.
    FIELD is the name of the field to filter on.
    COMP can be lt, lte, gt, or gte.""")
@click.option('--std-quality',
              is_flag=True,
              default=False,
              show_default=True,
              help='Filter to standard quality.')
@click.option('--string-in',
              type=click.Tuple([types.Field(), types.CommaSeparatedString()]),
              multiple=True,
              callback=string_in_to_filter,
              help="""Filter field by numeric in.
    FIELD is the name of the field to filter on.
    VALUE is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option(
    '--update',
    type=click.Tuple([types.Field(), types.GTComparison(), types.DateTime()]),
    callback=update_to_filter,
    multiple=True,
    help="""Filter to items with changes to a specified field value made after
    a specified date.
    FIELD is the name of the field to filter on.
    COMP can be gt or gte.
    DATETIME can be an RFC3339 or ISO 8601 string.""")
@pretty
def filter(ctx,
           asset,
           date_range,
           geom,
           number_in,
           nrange,
           string_in,
           update,
           permission,
           pretty,
           std_quality):
    """Create a structured item search filter.

    This command provides basic functionality for specifying a filter by
    creating an AndFilter with the filters identified with the options as
    inputs. This is only a subset of the complex filtering supported by the
    API. For advanced filter creation, either create the filter by hand or use
    the Python API.

    If no options are specified, an empty filter is returned which, when used
    in a search, bypasses all search filtering.
    """
    permission = data_filter.permission_filter() if permission else None
    std_quality = data_filter.std_quality_filter() if std_quality else None

    filter_options = (asset,
                      date_range,
                      geom,
                      number_in,
                      nrange,
                      string_in,
                      update,
                      permission,
                      std_quality)

    # options allowing multiples are broken up so one filter is created for
    # each time the option is specified
    # unspecified options are skipped
    filters = []
    for f in filter_options:
        if f:
            if isinstance(f, list):
                filters.extend(f)
            else:
                filters.append(f)

    if filters:
        filt = data_filter.and_filter(filters)
    else:
        # make it explicit that we return an empty filter
        # when no filters are specified
        filt = data_filter.empty_filter()

    echo_json(filt, pretty)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.option("--geom", type=types.Geometry(), callback=check_geom)
@click.option('--filter',
              type=types.JSON(),
              help="""Apply specified filter to search. Can be a json string,
              filename, or '-' for stdin.""")
@limit
@click.option('--name', type=str, help='Name of the saved search.')
@click.option('--sort',
              type=click.Choice(SEARCH_SORT),
              default=SEARCH_SORT_DEFAULT,
              show_default=True,
              help='Field and direction to order results by.')
@pretty
async def search(ctx, item_types, geom, filter, limit, name, sort, pretty):
    """Execute a structured item search.

    This function outputs a series of GeoJSON descriptions, one for each of the
    returned items, optionally pretty-printed.

    ITEM_TYPES is a comma-separated list of item-types to search.

    If --filter is specified, the filter must be JSON and can be a json string,
    filename, or '-' for stdin. If not specified, search results are not
    filtered.

    Quick searches are stored for approximately 30 days and the --name
    parameter will be applied to the stored quick search.
    """
    async with data_client(ctx) as cl:

        async for item in cl.search(item_types,
                                    geometry=geom,
                                    search_filter=filter,
                                    name=name,
                                    sort=sort,
                                    limit=limit):
            echo_json(item, pretty)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.option("--geom", type=types.Geometry(), callback=check_geom)
@click.option(
    '--filter',
    type=types.JSON(),
    required=True,
    help="""Filter to apply to search. Can be a json string, filename,
         or '-' for stdin.""")
@click.option('--name',
              type=str,
              required=True,
              help='Name of the saved search.')
@click.option('--daily-email',
              is_flag=True,
              help='Send a daily email when new results are added.')
@pretty
async def search_create(ctx,
                        item_types,
                        geom,
                        filter,
                        name,
                        daily_email,
                        pretty):
    """Create a new saved structured item search.

    This function outputs a full JSON description of the created search,
    optionally pretty-printed.

    ITEM_TYPES is a comma-separated list of item-types to search.
    """
    async with data_client(ctx) as cl:
        items = await cl.create_search(item_types=item_types,
                                       geometry=geom,
                                       search_filter=filter,
                                       name=name,
                                       enable_email=daily_email)
        echo_json(items, pretty)


@data.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.option('--sort',
              type=click.Choice(LIST_SORT_ORDER),
              default=LIST_SORT_DEFAULT,
              show_default=True,
              help='Field and direction to order results by.')
@click.option('--search-type',
              type=click.Choice(LIST_SEARCH_TYPE),
              default=LIST_SEARCH_TYPE_DEFAULT,
              show_default=True,
              help='Search type filter.')
@limit
@pretty
async def search_list(ctx, sort, search_type, limit, pretty):
    """List saved searches.

    This function outputs a full JSON description of the saved searches,
    optionally pretty-printed.
    """
    async with data_client(ctx) as cl:
        async for item in cl.list_searches(sort=sort,
                                           search_type=search_type,
                                           limit=limit):
            echo_json(item, pretty)


@data.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('search_id', callback=check_search_id)
@click.option('--sort',
              type=click.Choice(SEARCH_SORT),
              default=SEARCH_SORT_DEFAULT,
              show_default=True,
              help='Field and direction to order results by.')
@limit
@pretty
async def search_run(ctx, search_id, sort, limit, pretty):
    """Execute a saved structured item search.

    This function outputs a series of GeoJSON descriptions, one for each of the
    returned items, optionally pretty-printed.
    """
    async with data_client(ctx) as cl:
        async for item in cl.run_search(search_id, sort=sort, limit=limit):
            echo_json(item, pretty)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.option(
    '--filter',
    type=types.JSON(),
    required=True,
    help="""Filter to apply to search. Can be a json string, filename,
         or '-' for stdin.""")
@click.option('--interval',
              type=click.Choice(STATS_INTERVAL),
              required=True,
              help='The size of the histogram date buckets.')
async def stats(ctx, item_types, filter, interval):
    """Get a bucketed histogram of items matching the filter.

    This function returns a bucketed histogram of results based on the
    item_types, interval, and filter specified.

    """
    async with data_client(ctx) as cl:
        items = await cl.get_stats(item_types=item_types,
                                   search_filter=filter,
                                   interval=interval)
        echo_json(items)


@data.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument('search_id')
async def search_get(ctx, search_id, pretty):
    """Get a saved search.

    This function outputs a full JSON description of the identified saved
    search, optionally pretty-printed.
    """
    async with data_client(ctx) as cl:
        items = await cl.get_search(search_id)
        echo_json(items, pretty)


@data.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('search_id')
async def search_delete(ctx, search_id):
    """Delete an existing saved search.
    """
    async with data_client(ctx) as cl:
        await cl.delete_search(search_id)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('search_id')
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.option(
    '--filter',
    type=types.JSON(),
    required=True,
    help="""Filter to apply to search. Can be a json string, filename,
         or '-' for stdin.""")
@click.option('--name',
              type=str,
              required=True,
              help='Name of the saved search.')
@click.option("--geom",
              type=types.Geometry(),
              callback=check_geom,
              default=None)
@click.option('--daily-email',
              is_flag=True,
              help='Send a daily email when new results are added.')
@pretty
async def search_update(ctx,
                        search_id,
                        item_types,
                        filter,
                        geom,
                        name,
                        daily_email,
                        pretty):
    """Update a saved search with the given search request.

    This function outputs a full JSON description of the updated search,
    optionally pretty-printed.
    """
    async with data_client(ctx) as cl:
        items = await cl.update_search(search_id,
                                       item_types,
                                       search_filter=filter,
                                       name=name,
                                       geometry=geom,
                                       enable_email=daily_email)
        echo_json(items, pretty)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_type", type=str, callback=check_item_type)
@click.argument("item_id")
@click.argument("asset_type")
@click.option('--directory',
              default='.',
              help=('Base directory for file download.'),
              type=click.Path(exists=True,
                              resolve_path=True,
                              writable=True,
                              file_okay=False))
@click.option('--filename',
              default=None,
              help=('Custom name to assign to downloaded file.'),
              type=str)
@click.option('--overwrite',
              is_flag=True,
              default=False,
              help=('Overwrite files if they already exist.'))
@click.option('--checksum',
              is_flag=True,
              default=None,
              help=('Verify that checksums match.'))
async def asset_download(ctx,
                         item_type,
                         item_id,
                         asset_type,
                         directory,
                         filename,
                         overwrite,
                         checksum):
    """Download an activated asset.

    This function will fail if the asset state is not activated. Consider
    calling `asset-wait` before this command to ensure the asset is activated.

    If --checksum is provided, the associated checksums given in the manifest
    are compared against the downloaded files to verify that they match.

    If --checksum is provided, files are already downloaded, and --overwrite is
    not specified, this will simply validate the checksums of the files against
    the manifest.

    Output:
    The full path of the downloaded file. If the quiet flag is not set, this
    also provides ANSI download status reporting.
    """
    quiet = ctx.obj['QUIET']
    async with data_client(ctx) as cl:
        asset = await cl.get_asset(item_type, item_id, asset_type)
        path = await cl.download_asset(asset=asset,
                                       filename=filename,
                                       directory=Path(directory),
                                       overwrite=overwrite,
                                       progress_bar=not quiet)
        if checksum:
            cl.validate_checksum(asset, path)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_type", type=str, callback=check_item_type)
@click.argument("item_id")
@click.argument("asset_type")
async def asset_activate(ctx, item_type, item_id, asset_type):
    """Activate an asset."""
    async with data_client(ctx) as cl:
        asset = await cl.get_asset(item_type, item_id, asset_type)
        await cl.activate_asset(asset)


@data.command(epilog=valid_item_string)  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_type", type=str, callback=check_item_type)
@click.argument("item_id")
@click.argument("asset_type")
@click.option('--delay',
              type=int,
              default=5,
              help='Time (in seconds) between polls.')
@click.option('--max-attempts',
              type=int,
              default=200,
              show_default=True,
              help='Maximum number of polls. Set to zero for no limit.')
async def asset_wait(ctx, item_type, item_id, asset_type, delay, max_attempts):
    """Wait for an asset to be activated.

    Returns when the asset status has reached "activated" and the asset is
    available.
    """
    quiet = ctx.obj['QUIET']
    async with data_client(ctx) as cl:
        asset = await cl.get_asset(item_type, item_id, asset_type)
        with AssetStatusBar(item_type, item_id, asset_type,
                            disable=quiet) as bar:
            status = await cl.wait_asset(asset,
                                         delay,
                                         max_attempts,
                                         callback=bar.update)
    click.echo(status)


# @data.command()
# @click.pass_context
# @translate_exceptions
# @coro
# @click.argument("item_type")
# @click.argument("item_id")
# @click.argument("asset_type_id")
# @pretty
# async def asset_get(ctx, item_type, item_id, asset_type_id, pretty):
#     """Get an item asset."""
#     async with data_client(ctx) as cl:
#         asset = await cl.get_asset(item_type, item_id, asset_type_id)
#     echo_json(asset, pretty)

# TODO: search_run()".
# TODO: item_get()".
