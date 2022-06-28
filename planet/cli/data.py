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
from typing import List, Optional
from contextlib import asynccontextmanager

import click

from planet import data_filter, exceptions, io, DataClient
from .cmds import coro, translate_exceptions
from .io import echo_json
from .session import CliSession

pretty = click.option('--pretty', is_flag=True, help='Pretty-print output.')


@asynccontextmanager
async def data_client(ctx):
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']
    async with CliSession(auth=auth) as sess:
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
    ctx.obj['AUTH'] = None
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
    """Clarify that this entry is for a field"""
    name = 'field'


class ComparisonType(click.ParamType):
    name = 'comp'
    valid = ['lt', 'lte', 'gt', 'gte']

    def convert(self, value, param, ctx) -> str:
        if value not in self.valid:
            self.fail(f'COMP ({value}) must be one of {",".join(self.valid)}',
                      param,
                      ctx)
        return value


class GTComparisonType(ComparisonType):
    """Only support gt or gte comparison"""
    valid = ['gt', 'gte']


class DateTimeType(click.ParamType):
    name = 'datetime'

    def convert(self, value, param, ctx) -> datetime:
        if not isinstance(value, datetime):
            try:
                value = io.str_to_datetime(value)
            except exceptions.PlanetError as e:
                self.fail(str(e))

        return value


class CommaSeparatedString(click.types.StringParamType):
    """A list of strings that is extracted from a comma-separated string."""

    def convert(self, value, param, ctx) -> List[str]:
        value = super().convert(value, param, ctx)

        if not isinstance(value, list):
            value = [part.strip() for part in value.split(",")]

        return value


class CommaSeparatedFloat(click.types.StringParamType):
    """A list of floats that is extracted from a comma-separated string."""
    name = 'VALUE'

    def convert(self, value, param, ctx) -> List[float]:
        values = CommaSeparatedString().convert(value, param, ctx)

        try:
            ret = [float(v) for v in values]
        except ValueError:
            self.fail(f'Cound not convert all entries in {value} to float.')

        return ret


def assets_to_filter(ctx, param, assets: List[str]) -> Optional[dict]:
    # TODO: validate and normalize
    return data_filter.asset_filter(assets) if assets else None


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
@pretty
@click.option('--asset',
              type=CommaSeparatedString(),
              default=None,
              callback=assets_to_filter,
              help="""Filter to items with one or more of specified assets.
    VALUE is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option('--date-range',
              type=click.Tuple([FieldType(), ComparisonType(),
                                DateTimeType()]),
              callback=date_range_to_filter,
              multiple=True,
              help="""Filter by date range in field.
    FIELD is the name of the field to filter on.
    COMP can be lt, lte, gt, or gte.
    DATETIME can be an RFC3339 or ISO 8601 string.""")
@click.option('--geom',
              type=str,
              default=None,
              callback=geom_to_filter,
              help='Filter to items that overlap a given geometry.')
@click.option('--number-in',
              type=click.Tuple([FieldType(), CommaSeparatedFloat()]),
              multiple=True,
              callback=number_in_to_filter,
              help="""Filter field by numeric in.
    FIELD is the name of the field to filter on.
    VALUE is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option('--range',
              'nrange',
              type=click.Tuple([FieldType(), ComparisonType(), float]),
              callback=range_to_filter,
              multiple=True,
              help="""Filter by date range in field.
    FIELD is the name of the field to filter on.
    COMP can be lt, lte, gt, or gte.
    DATETIME can be an RFC3339 or ISO 8601 string.""")
@click.option('--string-in',
              type=click.Tuple([FieldType(), CommaSeparatedString()]),
              multiple=True,
              callback=string_in_to_filter,
              help="""Filter field by numeric in.
    FIELD is the name of the field to filter on.
    VALUE is a comma-separated list of entries.
    When multiple entries are specified, an implicit 'or' logic is applied.""")
@click.option(
    '--update',
    type=click.Tuple([FieldType(), GTComparisonType(), DateTimeType()]),
    callback=update_to_filter,
    multiple=True,
    help="""Filter to items with changes to a specified field value made after
    a specified date.
    FIELD is the name of the field to filter on.
    COMP can be gt or gte.
    DATETIME can be an RFC3339 or ISO 8601 string.""")
@click.option('--permission',
              type=bool,
              default=True,
              show_default=True,
              help='Filter to assets with download permissions.')
@click.option('--std-quality',
              type=bool,
              default=True,
              show_default=True,
              help='Filter to standard quality.')
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
