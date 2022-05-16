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
from typing import Any, Callable, List, Union

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


def _range_filter(
    ftype: str,
    field_name: str,
    gt: Any,
    lt: Any,
    gte: Any,
    lte: Any,
    callback: Callable = None,
) -> dict:
    """Base for creating range filters

    Parameters:
        ftype: Type of the filter
        field_name: Name of field to filter on.
        gt: Greater than conditional value.
        lt: Less than conditional value.
        gte: Greater than or equal to conditional value.
        lte: Less than or equal to conditional value.
        callback: Function to apply to preprocess conditional values.

    Raises:
        exceptions.PlanetError: If no conditional parameter is specified.
    """
    conditionals = {'gt': gt, 'lt': lt, 'gte': gte, 'lte': lte}

    # if callback isn't specified, just use a passthrough
    callback = callback if callback else lambda x: x

    config = {
        key: callback(value)
        for (key, value) in conditionals.items() if value is not None
    }

    if not config:
        raise exceptions.PlanetError("No conditional parameters specified.")

    return _field_filter(ftype, field_name=field_name, config=config)


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
        field_name: Name of field to filter on.
        gt: Filter to field timestamp later than this datetime.
        lt: Filter to field timestamp earlier than this datetime.
        gte: Filter to field timestamp at or later than this datetime.
        lte: Filter to field timestamp at or earlier than this datetime.

    Raises:
        exceptions.PlanetError: If no conditional parameter is specified.
    """
    return _range_filter('DateRangeFilter',
                         field_name,
                         gt,
                         lt,
                         gte,
                         lte,
                         callback=_datetime_to_rfc3339)


def _datetime_to_rfc3339(value: datetime) -> str:
    """Converts the datetime to an RFC3339 string"""
    iso = value.isoformat()
    if not value.utcoffset():
        # rfc3339 needs a Z if there is no timezone offset
        iso += 'Z'
    return iso


def range_filter(field_name: str,
                 gt: float = None,
                 lt: float = None,
                 gte: float = None,
                 lte: float = None) -> dict:
    """Create a RangeFilter

    The RangeFilter can be used to search for items with numerical properties.
    It is useful for matching fields that have a continuous range of values
    such as cloud_cover or view_angle.

    One or more of the conditional parameters `gt`, `lt`, `gte`, `lte` must be
    specified.

    Parameters:
        field_name: Name of field to filter on.
        gt: Filter to field value greater than this number.
        lt: Filter to field value less than this number.
        gte: Filter to field value greater than or equal to this number.
        lte: Filter to field value less than or equal to this number.

    Raises:
        exceptions.PlanetError: If no conditional parameter is specified.
    """
    return _range_filter('RangeFilter', field_name, gt, lt, gte, lte)


def update_filter(field_name: str,
                  gt: float = None,
                  lt: float = None,
                  gte: float = None,
                  lte: float = None) -> dict:
    """Create an UpdateFilter

    The UpdateFilter can be used to filter items by changes to a specified
    metadata field value made after a specified date, due to a republishing
    event. This feature allows you identify items which may have been
    republished with improvements or fixes, enabling you to keep your internal
    catalogs up-to-date and make more informed redownload decisions. The filter
    works for all items published on or after April 10, 2020.

    One or more of the conditional parameters `gt` or `gte` must be
    specified.

    Parameters:
        field_name: Name of field to filter on.
        gt: Filter to changes to field metadata after this datetime.
        gte: Filter to changes to field metadata at or after this datetime.

    Raises:
        exceptions.PlanetError: If no conditional parameter is specified.
    """
    return _range_filter('UpdateFilter',
                         field_name,
                         gt,
                         None,
                         gte,
                         None,
                         callback=_datetime_to_rfc3339)
