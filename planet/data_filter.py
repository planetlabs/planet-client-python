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
"""Functionality for preparing a data search filter"""
import logging
from typing import Any, List

from planet import exceptions

LOGGER = logging.getLogger(__name__)


def _logicalfilter(ftype: str, nested_filters: List[dict]) -> dict:
    return {'type': ftype, 'config': nested_filters}


def and_filter(nested_filters: List[dict]) -> dict:
    """Create an AndFilter

    The AndFilter can be used to limit results to items with properties or
    permissions which match all nested filters.

    It is most commonly used as a top-level filter to ensure criteria across
    all field and permission filters are met.

    Parameters:
        nested_filters: Filters to AND together
    """
    return _logicalfilter('AndFilter', nested_filters)


def or_filter(nested_filters: List[dict]) -> dict:
    """Create an OrFilter

    The OrFilter can be used to match items with properties or permissions
    which match at least one of the nested filters.

    Parameters:
        nested_filters: Filters to OR together
    """
    return _logicalfilter('OrFilter', nested_filters)


def not_filter(nested_filter: dict):
    """Create a NotFilter

    The NotFilter can be used to match items with properties or permissions
    which do not match the nested filter.

    This filter only supports a single nested filter. Multiple NotFilters can
    be nested within an AndFilter to filter across multiple fields or
    permission values.

    Parameters:
        nested_filter: Filter to NOT
    """
    return _logicalfilter('NotFilter', nested_filter)


def _field_filter(ftype: str, field_name: str, config: Any[dict,
                                                           list]) -> dict:
    return {'type': ftype, 'field_name': field_name, 'config': config}


def date_range_filter(field_name: str,
                      gt: str = None,
                      lt: str = None,
                      gte: str = None,
                      lte: str = None) -> dict:
    """Create a DateRangeFilter

    The DateRangeFilter can be used to search on any property with a timestamp
    such as acquired or published.

    The filter's configuration is a nested structure with optional keys: gte,
    gt, lt or lte. Each corresponding value is an RFC 3339 date.

    Predicate arguments accept a str that is ISO-8601 format or a value
    that has an `isoformat` callable that returns an ISO-8601 compliant str.
    If no timezone is provided, UTC is assumed for RFC 3339 compatability.

    Parameters:
        field_name: Name of field to filter on
        gt: Filter to field values greater than this value
        lt: Filter to field values less than this value
        gte: Filter to field values greater than or equal to this value
        lte: Filter to field values less than or equal to this value

    """
    conditionals = {'gt': gt, 'lt': lt, 'gte': gte, 'lte': lte}

    if all(v is None for v in conditionals.values):
        raise exceptions.PlanetError("Must specify one of gt, lt, gte, or lte")

    config = {
        key: _to_rfc3339_date(value)
        for (key, value) in conditionals if value
    }

    return _field_filter('DateRangeFilter',
                         field_name=field_name,
                         config=config)


def _to_rfc3339_date(value):
    raise NotImplementedError


