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
from datetime import datetime
import logging
from typing import List, Union

from planet import exceptions

LOGGER = logging.getLogger(__name__)


def and_filter(nested_filters: List[dict]) -> dict:
    """Create an AndFilter

    The AndFilter can be used to limit results to items with properties or
    permissions which match all nested filters.

    It is most commonly used as a top-level filter to ensure criteria across
    all field and permission filters are met.

    Parameters:
        nested_filters: Filters to AND together
    """
    return {'type': 'AndFilter', 'config': nested_filters}


def or_filter(nested_filters: List[dict]) -> dict:
    """Create an OrFilter

    The OrFilter can be used to match items with properties or permissions
    which match at least one of the nested filters.

    Parameters:
        nested_filters: Filters to OR together
    """
    return {'type': 'OrFilter', 'config': nested_filters}


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
    return {'type': 'NotFilter', 'config': nested_filter}


def _field_filter(ftype: str, field_name: str, config: Union[dict,
                                                             list]) -> dict:
    return {'type': ftype, 'field_name': field_name, 'config': config}


def date_range_filter(field_name: str,
                      gt: datetime = None,
                      lt: datetime = None,
                      gte: datetime = None,
                      lte: datetime = None) -> dict:
    """Create a DateRangeFilter

    The DateRangeFilter can be used to search on any property with a timestamp
    such as acquired or published.

    One or more of the conditional parameters `gt`, `lt`, `gte`, `lte` must be
    specified.

    Parameters:
        field_name: Name of field to filter on
        gt: Filter to field timestamp later than this value
        lt: Filter to field timestamp earlier than this value
        gte: Filter to field timestamp at or later than this value
        lte: Filter to field timestamp at or earlier than this value

    Raises:
        exceptions.PlanetError: If no conditional parameter is specified.
    """
    conditionals = {'gt': gt, 'lt': lt, 'gte': gte, 'lte': lte}

    if all(v is None for v in conditionals.values()):
        raise exceptions.PlanetError("Must specify one of gt, lt, gte, or lte")

    config = {
        key: datetime_to_rfc3339(value)  # convert datetime to RFC3339 string
        for (key, value) in conditionals.items() if value
    }

    LOGGER.warning(config)

    return _field_filter('DateRangeFilter',
                         field_name=field_name,
                         config=config)


def datetime_to_rfc3339(value: datetime) -> str:
    """Converts the datetime to an RFC3339 string"""
    iso = value.isoformat()
    if not value.utcoffset():
        # rfc3339 needs a Z if there is no timezone offset
        iso += 'Z'
    return iso
