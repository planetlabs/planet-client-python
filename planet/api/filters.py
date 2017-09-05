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

from .utils import strp_lenient


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
    all_items = list(set(filter_like.get('item_types', [])).union(item_types))
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
    '''Build an `and` filter from the provided predicate filters.

    >>> filt = and_filter(
    ...   range_filter('cloud_cover', gt=0.1),
    ...   range_filter('cloud_cover', lt=0.2)
    ... )
    >>> filt['type']
    'AndFilter'
    >>> filt['config'][0] == \
    {'config': {'gt': 0.1}, 'field_name': 'cloud_cover', 'type': 'RangeFilter'}
    True
    >>> filt['config'][1] == \
    {'config': {'lt': 0.2}, 'field_name': 'cloud_cover', 'type': 'RangeFilter'}
    True
    '''
    return _filter('AndFilter', predicates)


def or_filter(*predicates):
    ''' Build an `or` filter from the provided predicate filters.

    >>> import datetime
    >>> n = datetime.datetime(year=2017, month=2, day=14)
    >>> filt = or_filter(
    ...   date_range('acquired', gt=n),
    ...   range_filter('cloud_cover', gt=0.1),
    ... )
    >>> filt['type']
    'OrFilter'
    >>> filt['config'][0] == \
    {'config': {'gt': '2017-02-14T00:00:00Z'}, 'field_name': 'acquired', \
    'type': 'DateRangeFilter'}
    True
    >>> filt['config'][1] == \
    {'config': {'gt': 0.1}, 'field_name': 'cloud_cover', 'type': 'RangeFilter'}
    True
    '''
    return _filter('OrFilter', predicates)


def not_filter(*predicates):
    return _filter('NotFilter', predicates)


def date_range(field_name, **kwargs):
    '''Build a DateRangeFilter.

    Predicate arguments accept a value str that in ISO-8601 format or a value
    that has a `isoformat` callable that returns an ISO-8601 str.

    :raises: ValueError if predicate value does not parse

    >>> date_range('acquired', gt='2017') == \
    {'config': {'gt': '2017-01-01T00:00:00Z'}, \
    'field_name': 'acquired', 'type': 'DateRangeFilter'}
    True
    '''
    for k, v in kwargs.items():
        dt = v
        if not hasattr(v, 'isoformat'):
            dt = strp_lenient(str(v))
            if dt is None:
                raise ValueError("unable to use provided time: " + str(v))
        kwargs[k] = dt.isoformat() + 'Z'
    return _filter('DateRangeFilter', config=kwargs, field_name=field_name)


def range_filter(field_name, **kwargs):
    '''Build a RangeFilter.

    >>> range_filter('cloud_cover', gt=0.1) == \
    {'config': {'gt': 0.1}, 'field_name': 'cloud_cover', 'type': 'RangeFilter'}
    True
    '''
    return _filter('RangeFilter', config=kwargs, field_name=field_name)


def geom_filter(geom, field_name=None):
    '''Build a GeometryFilter from the provided geosjon geom dict.

    :param geojson geom: the geojson geom dict
    :param str field_name: optional field name, default is 'geometry'
    '''
    return _filter('GeometryFilter', config=geom,
                   field_name=field_name or 'geometry')


def num_filter(field_name, *vals):
    '''Build a NumberInFilter.

    >>> num_filter('value', 50, 100) == \
    {'config': (50, 100), 'field_name': 'value', 'type': 'NumberInFilter'}
    True
    '''
    return _filter('NumberInFilter', config=vals, field_name=field_name)


def permission_filter(*perms):
    '''Build a PermissionFilter with the specified permissions.

    >>> permission_filter('assets:download') == \
    {'type': 'PermissionFilter', 'config': ('assets:download',)}
    True
    '''
    return _filter('PermissionFilter', config=perms)


def string_filter(field_name, *vals):
    '''Build a StringInFilter.

    >>> string_filter('id', 'id1', 'id2', 'id3') == \
    {'config': ('id1', 'id2', 'id3'), 'field_name': 'id', \
    'type': 'StringInFilter'}
    True
    '''
    return _filter('StringInFilter', config=vals, field_name=field_name)
