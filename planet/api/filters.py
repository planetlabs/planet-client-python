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


def build_search_request(filter_like, item_types, name=None, interval=None):
    '''Build a data-api search request body for the specified item_types.
    If 'filter_like' is a request, item_types will be merged and, if name or
    interval is provided, will replace any existing values.

    :param dict filter_like: a filter or request with a filter
    :param sequence(str) item_types: item-types to specify in the request
    :param str name: optional name
    :param str interval: optional interval [year, month, week, day]
    '''
    filter_spec = filter_like.get('filter', filter_like)
    all_items = list(set(filter_like.get('item_types', [])).union(*item_types))
    name = filter_like.get('name', name)
    interval = filter_like.get('interval', interval)
    req = {'item_types': all_items, 'filter': filter_spec}
    if name:
        req['name'] = name
    if interval:
        req['interval'] = interval
    return req


def is_filter_like(filter_like):
    '''Check if the provided dict looks like a search request or filter.'''
    if 'item_types' in filter_like or 'filter' in filter_like:
        filter_like = filter_like.get('filter', {})
    return 'type' in filter_like and 'config' in filter_like


def _filter(ftype, config=None, **kwargs):
    kwargs.update({
        'type': ftype,
        'config': config,
    })
    return kwargs


def and_filter(*predicates):
    return _filter("AndFilter", predicates)


def or_filter(*predicates):
    return _filter("OrFilter", predicates)


def not_filter(*predicates):
    return _filter("NotFilter", predicates)


def date_range(field_name, **kwargs):
    for k, v in kwargs.items():
        if hasattr(v, 'isoformat'):
            # @todo check timezone handling
            kwargs[k] = v.isoformat() + 'Z'
    return _filter("DateRangeFilter", config=kwargs, field_name=field_name)


def range_filter(field_name, **kwargs):
    return _filter("RangeFilter", config=kwargs, field_name=field_name)


def geom_filter(geom, field_name=None):
    return _filter("GeometryFilter", config=geom,
                   field_name=field_name or "geometry")


def num_filter(field_name, *vals):
    return _filter("NumberInFilter", config=vals, field_name=field_name)


def string_filter(field_name, *vals):
    return _filter("StringInFilter", config=vals, field_name=field_name)
