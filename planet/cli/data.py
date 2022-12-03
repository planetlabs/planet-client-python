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

import click

from planet import data_filter, DataClient
from planet.clients.data import (SEARCH_SORT,
                                 SEARCH_SORT_DEFAULT,
                                 STATS_INTERVAL)
from planet.specs import (get_item_types,
                          validate_item_type,
                          SpecificationException)

from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession

ALL_ITEM_TYPES = get_item_types()
valid_item_string = "Valid entries for ITEM_TYPES: " + "|".join(ALL_ITEM_TYPES)


@asynccontextmanager
async def data_client(ctx):
    async with CliSession() as sess:
        cl = DataClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def data(ctx, base_url):
    '''Commands for interacting with the Data API'''
    ctx.obj['BASE_URL'] = base_url


# TODO: filter().
def geom_to_filter(ctx, param, value: Optional[dict]) -> Optional[dict]:
    return data_filter.geometry_filter(value) if value else None


def assets_to_filter(ctx, param, assets: List[str]) -> Optional[dict]:
    # TODO: validate and normalize
    return data_filter.asset_filter(assets) if assets else None


def check_item_types(ctx, param, item_types) -> Optional[List[dict]]:
    '''Validates the item type by comparing the inputted item type to all
    supported item types.'''
    try:
        for item_type in item_types:
            validate_item_type(item_type)
        return item_types
    except SpecificationException as e:
        raise click.BadParameter(str(e))


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


@data.command()
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
              type=bool,
              default=True,
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
              type=bool,
              default=True,
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

    filt = data_filter.and_filter(filters)
    echo_json(filt, pretty)


@data.command(epilog=valid_item_string)
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.argument("filter", type=types.JSON(), default="-", required=False)
@limit
@click.option('--name', type=str, help='Name of the saved search.')
@click.option('--sort',
              type=click.Choice(SEARCH_SORT),
              default=SEARCH_SORT_DEFAULT,
              show_default=True,
              help='Field and direction to order results by.')
@pretty
async def search(ctx, item_types, filter, limit, name, sort, pretty):
    """Execute a structured item search.

    This function outputs a series of GeoJSON descriptions, one for each of the
    returned items, optionally pretty-printed.

    ITEM_TYPES is a comma-separated list of item-types to search.

    FILTER must be JSON and can be specified a json string, filename, or '-'
    for stdin. It defaults to reading from stdin.

    Quick searches are stored for approximately 30 days and the --name
    parameter will be applied to the stored quick search.
    """
    async with data_client(ctx) as cl:

        async for item in cl.search(item_types,
                                    filter,
                                    name=name,
                                    sort=sort,
                                    limit=limit):
            echo_json(item, pretty)


@data.command(epilog=valid_item_string)
@click.pass_context
@translate_exceptions
@coro
@click.argument('name')
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.argument("filter", type=types.JSON(), default="-", required=False)
@click.option('--daily-email',
              is_flag=True,
              help='Send a daily email when new results are added.')
@pretty
async def search_create(ctx, name, item_types, filter, daily_email, pretty):
    """Create a new saved structured item search.

    This function outputs a full JSON description of the created search,
    optionally pretty-printed.

    NAME is the name to give the search.

    ITEM_TYPES is a comma-separated list of item-types to search.

    FILTER must be JSON and can be specified a json string, filename, or '-'
    for stdin. It defaults to reading from stdin.
    """
    async with data_client(ctx) as cl:
        items = await cl.create_search(name=name,
                                       item_types=item_types,
                                       search_filter=filter,
                                       enable_email=daily_email)
        echo_json(items, pretty)


@data.command(epilog=valid_item_string)
@click.pass_context
@translate_exceptions
@coro
@click.argument("item_types",
                type=types.CommaSeparatedString(),
                callback=check_item_types)
@click.argument('interval', type=click.Choice(STATS_INTERVAL))
@click.argument("filter", type=types.JSON(), default="-", required=False)
async def stats(ctx, item_types, interval, filter):
    """Get a bucketed histogram of items matching the filter.

    This function returns a bucketed histogram of results based on the
    item_types, interval, and json filter specified (using file or stdin).

    """
    async with data_client(ctx) as cl:
        items = await cl.get_stats(item_types=item_types,
                                   interval=interval,
                                   search_filter=filter)
        echo_json(items)


@data.command()
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


# TODO: search_update()".
# TODO: search_delete()".
# TODO: search_run()".
# TODO: item_get()".
# TODO: asset_activate()".
# TODO: asset_wait()".
# TODO: asset_download()".
