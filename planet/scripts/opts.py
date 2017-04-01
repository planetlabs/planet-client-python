# Copyright 2017 Planet Labs, Inc.
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

import click

from .types import (
    AssetType,
    AssetTypePerm,
    DateRange,
    GeomFilter,
    FilterJSON,
    ItemType,
    NumberIn,
    Range,
    SortSpec,
    StringIn
)


pretty = click.option('-pp/-r', '--pretty/--no-pretty', default=None,
                      is_flag=True, help='Format JSON output')

dest_dir = click.option('-d', '--dest', help='Destination directory',
                        type=click.Path(file_okay=False, resolve_path=True,
                                        exists=True))

num_type = type('number', (click.types.IntParamType,), {'name': 'number'})()


def limit_option(default):
    return click.option('--limit', default=default, required=False,
                        type=num_type, help="Limit the number of items.")


geom_filter = click.option('--geom', type=GeomFilter(), help=(
    'Specify a geometry filter as geojson.'
))

date_range_filter = click.option(
    '--date', nargs=3, multiple=True, type=DateRange(),
    help=(
        'Filter field by date.'
    )
)

range_filter = click.option(
    '--range', multiple=True, type=Range(),
    help=(
        'Filter field by numeric range.'
    )
)

number_in_filter = click.option(
    '--number-in', multiple=True, type=NumberIn(),
    help=(
        'Filter field by numeric in.'
    )
)

string_in_filter = click.option(
    '--string-in', multiple=True, type=StringIn(),
    help=(
        'Filter field by string in.'
    )
)

item_type_option = click.option(
    '--item-type', multiple=True, required=True, type=ItemType(), help=(
       'Specify item type(s)'
    )
)

asset_type_option = click.option(
    '--asset-type', multiple=True, required=True, type=AssetType(), help=(
        'Specify asset type(s)'
    )
)

asset_type_perms = click.option(
    '--asset-type', multiple=True, required=False, type=AssetTypePerm(), help=(
        'Specify asset type(s) permissions'
    )
)

# @todo add validate/parse
filter_json_option = click.option(
    '--filter-json', default='@-', type=FilterJSON(), help=(
        'Use the specified filter'
    )
)

ndjson_option = click.option('--ndjson', is_flag=True, help=(
    'Request output as new-line delimited json.'
))


sort_order = click.option(
    '--sort', type=SortSpec(), help=(
        'Specify sort ordering as published/acquired asc/desc'
    )
)

_filter_opts = [date_range_filter, range_filter, number_in_filter,
                string_in_filter, geom_filter, filter_json_option]


def filter_opts(fun):
    '''Decorator for all search filter options'''
    for o in _filter_opts:
        fun = o(fun)
    return fun


def search_request_opts(fun):
    '''Decorator for common search request options'''
    return sort_order(item_type_option(filter_opts(fun)))
