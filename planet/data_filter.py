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
from typing import Optional, Any, Callable, List, Union

from planet import exceptions, geojson

LOGGER = logging.getLogger(__name__)


def empty_filter() -> dict:
    """Create an Empty filter for bypassing search filtering."""
    return {'type': 'AndFilter', 'config': []}


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
    callback: Optional[Callable] = None,
) -> dict:
    """Base for creating range filters.

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
                      gt: Optional[datetime] = None,
                      lt: Optional[datetime] = None,
                      gte: Optional[datetime] = None,
                      lte: Optional[datetime] = None) -> dict:
    """Create a DateRangeFilter

    The DateRangeFilter can be used to search on any property with a timestamp
    such as acquired or published.

    One or more of the conditional parameters `gt`, `lt`, `gte`, `lte` must be
    specified. Conditionals are combined in a logical AND, so only items that
    match all specified conditionals are returned.

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
    if value.utcoffset() is None:
        # rfc3339 needs a Z if there is no timezone offset
        iso += 'Z'
    return iso


def range_filter(field_name: str,
                 gt: Optional[float] = None,
                 lt: Optional[float] = None,
                 gte: Optional[float] = None,
                 lte: Optional[float] = None) -> dict:
    """Create a RangeFilter

    The RangeFilter can be used to search for items with numerical properties.
    It is useful for matching fields that have a continuous range of values
    such as cloud_cover or view_angle.

    One or more of the conditional parameters `gt`, `lt`, `gte`, `lte` must be
    specified. Conditionals are combined in a logical AND, so only items that
    match all specified conditionals are returned.

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
                  gt: Optional[float] = None,
                  lt: Optional[float] = None,
                  gte: Optional[float] = None,
                  lte: Optional[float] = None) -> dict:
    """Create an UpdateFilter

    The UpdateFilter can be used to filter items by changes to a specified
    metadata field value made after a specified date, due to a republishing
    event. This feature allows you identify items which may have been
    republished with improvements or fixes, enabling you to keep your internal
    catalogs up-to-date and make more informed redownload decisions. The filter
    works for all items published on or after April 10, 2020.

    One or more of the conditional parameters `gt` or `gte` must be
    specified. Conditionals are combined in a logical AND, so only items that
    match all specified conditionals are returned.

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


def geometry_filter(geom: dict) -> dict:
    """Create a GeometryFilter

    The GeometryFilter can be used to search for items with a footprint
    geometry which intersects with the specified geometry.

    In cases where a GeoJSON Feature or FeatureCollection are provided, the
    GeoJSON geometry will be extracted and used in the filter definition.

    The filter's configuration supports Point, MultiPoint, LineString,
    MultiLineString, Polygon, and MultiPolygon GeoJSON object. For best
    results, the geometry should meet OpenGIS Simple Features Interface
    Specification requirements. If an invalid GeoJSON object is supplied, the
    API will automatically attempt to correct the geometry and return matching
    search results.

    Parameters:
        geom: GeoJSON describing the filter geometry, feature, or feature
            collection.
    """
    geom_filter = _field_filter('GeometryFilter',
                                field_name='geometry',
                                config=geojson.validate_geom_as_geojson(geom))
    return geom_filter


def number_in_filter(field_name: str, values: List[float]) -> dict:
    """Create a NumberInFilter

    The NumberInFilter can be used to search for items with numerical
    poperties. It is useful for matching fields such as gsd.

    Parameters:
        field_name: Name of field to filter on.
        values: List of numbers to filter on.
    """
    return _field_filter('NumberInFilter',
                         field_name=field_name,
                         config=values)


def string_in_filter(field_name: str, values: List[str]) -> dict:
    """Create a StringInFilter

    The StringInFilter can be used to search for items with string properties
    such as instrument or quality_category. Boolean properties such as
    ground_control are also supported with the StringInFilter.

    Filters to items with the given field matching any of the values.

    Parameters:
        field_name: Name of field to filter on.
        values: List of strings to filter on.
    """
    return _field_filter('StringInFilter',
                         field_name=field_name,
                         config=values)


def asset_filter(asset_types: List[str]) -> dict:
    """Create an AssetFilter

    The AssetFilter can be used to search for items which have published a
    specified asset_type. This filter is commonly used to filter items by
    published asset types which:

    * May be published at delay after an item's first publish. analytic_sr,
    for instance, may be published up to 12 hours after an item first becomes
    available.
    * May not be available for the full catalog. udm2, for instance, is only
    available globally through July 2018.

    Filters to all items which include any of the listed asset types. An
    AndFilter can be used to filter items by multiple asset types.

    Parameters:
        asset_types: List of the names of the asset type to filter on.
    """
    return {'type': 'AssetFilter', 'config': asset_types}


def permission_filter() -> dict:
    """Create a PermissionFilter

    The PermissionFilter limits results to items that a user has permission to
    download.
    """
    return {'type': 'PermissionFilter', 'config': ['assets:download']}


def std_quality_filter() -> dict:
    """Create a filter for standard-quality items.

    This is a custom filter which filters to items that are categorized as
    standard quality.
    """
    return string_in_filter('quality_category', ['standard'])
