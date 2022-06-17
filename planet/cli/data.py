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
from datetime import datetime
import json
from typing import List
from contextlib import asynccontextmanager

import click
import planet
from planet import data_filter, io, DataClient, Session

from .cmds import coro, translate_exceptions
from .io import echo_json

pretty = click.option('--pretty', is_flag=True, help='Pretty-print output.')


@asynccontextmanager
async def data_client(ctx):
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']
    async with Session(auth=auth) as sess:
        cl = DataClient(sess, base_url=base_url)
        yield cl


@click.group()
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def data(ctx, base_url):
    '''Commands for interacting with the Orders API'''
    ctx.obj['AUTH'] = planet.Auth.from_file()
    ctx.obj['BASE_URL'] = base_url


def parse_item_types(ctx, param, value: str) -> List[str]:
    """Turn a string of comma-separated names into a list of names."""
    # Note: we could also normalize case and validate the names against
    # our schema here.
    return [part.strip() for part in value.split(",")]


def parse_filter(ctx, param, value: str) -> dict:
    """Turn filter JSON into a dict."""
    # read filter using raw json
    if value.startswith('{'):
        try:
            json_value = json.loads(value)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Filter does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
        if json_value == {}:
            raise click.BadParameter('Filter is empty.', ctx=ctx, param=param)
        return json_value
    # read filter using click pipe option
    else:
        try:
            with click.open_file(value) as f:
                json_value = json.load(f)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Filter does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
        return json_value


def assets_to_filter(ctx, param, value: str) -> dict:
    if value is None:
        return value

    # manage assets as comma-separated names
    assets = [part.strip() for part in value.split(",")]
    return data_filter.asset_filter(assets)


def geom_to_filter(ctx, param, value: str) -> dict:
    if value is None:
        return value

    geom = _parse_geom(ctx, param, value)
    return data_filter.geometry_filter(geom)


def _parse_geom(ctx, param, value: str) -> dict:
    """Turn geom JSON into a dict."""
    # read from raw json
    if value.startswith('{'):
        try:
            json_value = json.loads(value)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('geom does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
        if json_value == {}:
            raise click.BadParameter('geom is empty.', ctx=ctx, param=param)
    # read from stdin or file
    else:
        try:
            with click.open_file(value) as f:
                json_value = json.load(f)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('geom does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
    return json_value


class FieldType(click.ParamType):
    name = 'field'
    help = 'FIELD is the name of the field to filter on.'

    def convert(self, value, param, ctx):
        return value


class ComparisonType(click.ParamType):
    name = 'comp'
    valid = ['lt', 'lte', 'gt', 'gte']
    help = 'COMP can be lt, lte, gt, or gte.'

    def convert(self, value, param, ctx):
        if value not in self.valid:
            self.fail(f'COMP ({value}) must be one of {",".join(self.valid)}',
                      param,
                      ctx)
        return value


class DateTimeType(click.ParamType):
    name = 'datetime'
    help = 'DATETIME can be an RFC 3339 or ISO 8601 string.'

    def convert(self, value, param, ctx):
        if isinstance(value, datetime):
            return value
        else:
            return io.str_to_datetime(value)


class DateRangeFilter(click.Tuple):
    help = ('Filter by date range in field. ' +
            f'{FieldType.help} {ComparisonType.help} {DateTimeType.help}')

    def __init__(self) -> None:
        super().__init__([FieldType(), ComparisonType(), DateTimeType()])

    def convert(self, value, param, ctx):
        vals = super().convert(value, param, ctx)

        field, comp, value = vals
        kwargs = {'field_name': field, comp: value}
        return data_filter.date_range_filter(**kwargs)


class RangeFilter(click.Tuple):
    help = ('Filter by number range in field. ' +
            f'{FieldType.help} {ComparisonType.help}')

    def __init__(self) -> None:
        super().__init__([FieldType(), ComparisonType(), float])

    def convert(self, value, param, ctx):
        vals = super().convert(value, param, ctx)

        field, comp, value = vals
        kwargs = {'field_name': field, comp: value}
        return data_filter.range_filter(**kwargs)


@data.command()
@click.pass_context
@translate_exceptions
@pretty
@click.option('--asset',
              type=str,
              default=None,
              callback=assets_to_filter,
              help='Filter to items with one or more of specified assets.')
# @click.option('--date-range',
#               type=DateRangeFilter(),
#               multiple=True,
#               help=DateRangeFilter.help)
@click.option('--geom',
              type=str,
              default=None,
              callback=geom_to_filter,
              help='Filter to items that overlap a given geometry.')
# @click.option('--range', 'nrange',
#               type=RangeFilter(),
#               multiple=True,
#               help=RangeFilter.help)
@click.option('--permission',
              type=bool,
              default=True,
              help='Filter to assets with download permissions.')
def filter(ctx, asset, geom, permission, pretty):
    """Create a structured item search filter.

    This command provides basic functionality for specifying a filter by
    creating an AndFilter with the filters identified with the options as
    inputs. This is only a subset of the complex filtering supported by the
    API. For advanced filter creation, either create the filter by hand or use
    the Python API.
    """
    permission = data_filter.permission_filter() if permission else None

    # options allowing multiples are broken up so one filter is created for
    # each time the option is specified
    filter_args = (asset, geom, permission)

    filters = [f for f in filter_args if f]

    if filters:
        if len(filters) > 1:
            filt = data_filter.and_filter(filters)
        else:
            filt = filters[0]
        echo_json(filt, pretty)


@data.command()
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument("item_types", callback=parse_item_types)
@click.argument("filter", callback=parse_filter)
@click.option('--name',
              type=str,
              default=False,
              help=('Name of the saved search.'))
@click.option('--limit',
              type=int,
              default=100,
              help='Maximum number of results to return. Defaults to 100.')
async def search_quick(ctx, item_types, filter, name, limit, pretty):
    """Execute a structured item search.

    This function executes a structured item search using the item_types,
    and json filter specified (using file or stdin).

    Quick searches are stored for approximately 30 days and the --name
    parameter will be applied to the stored quick search. This function
    outputs a series of GeoJSON descriptions, one for each of the returned
    items. The limit on the number of output items can be controlled using
    the "--limit" option, which defaults to 100 if limit is set to None or
    if the option is not used at all. If "--limit" is set to zero, no limit
    is applied and all results (a potentially large number) are returned.
    The output can also be optionally pretty-printed using "--pretty".
    """
    async with data_client(ctx) as cl:
        items = await cl.quick_search(name=name,
                                      item_types=item_types,
                                      search_filter=filter,
                                      limit=limit,
                                      sort=None)
        async for item in items:
            echo_json(item, pretty)


@data.command()
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument('name')
@click.argument("item_types", callback=parse_item_types)
@click.argument("filter", callback=parse_filter)
@click.option('--daily_email',
              is_flag=True,
              help='Send a daily email when new results are added.')
async def search_create(ctx, name, item_types, filter, daily_email, pretty):
    """Create a new saved structured item search.

    This function creates a new saved structured item search, using the
    name of the search, item_types, and json filter specified (using file or
    stdin). If specified, the "--daily_email" option enables users to recieve
    an email when new results are available each day. This function outputs a
    full JSON description of the created search. The output can also be
    optionally pretty-printed using "--pretty".
    """
    async with data_client(ctx) as cl:
        items = await cl.create_search(name=name,
                                       item_types=item_types,
                                       search_filter=filter,
                                       enable_email=daily_email)
        echo_json(items, pretty)


@data.command()
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument('search_id')
async def search_get(ctx, search_id, pretty):
    """Get a saved search.

    This function obtains an existing saved search, using the search_id.
    This function outputs a full JSON description of the identified saved
    search. The output can also be optionally pretty-printed using "--pretty".
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
# TODO: stats()".
