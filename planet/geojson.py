# Copyright 2021 Planet Labs, Inc.
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
"""Functionality for interacting with GeoJSON."""
import logging

import shapely.geometry as sgeom


LOGGER = logging.getLogger(__name__)


class GeoJSONException(Exception):
    '''invalid geojson'''
    pass


class WrongTypeException(GeoJSONException):
    '''wrong GeoJSON type'''
    pass


class MultipleFeaturesException(GeoJSONException):
    '''multiple features when only one is acceptable'''
    pass


def as_geom(data: dict) -> dict:
    """Extract the geometry from GeoJSON and validate.

    Parameters:
        data: GeoJSON geometry, Feature, or FeatureClass.

    Returns:
        GeoJSON geometry.

    Raises:
        GeoJSONException: If data is not valid GeoJSON geometry, Feature,
            or FeatureClass.
        DataLossWarning: If more than one Feature is in a FeatureClass.
    """
    geom = geom_from_geojson(data)
    validate_geom(geom)
    return geom


def as_polygon(data: dict) -> dict:
    geom = as_geom(data)
    geom_type = geom['type']
    if geom_type.lower() != 'polygon':
        raise WrongTypeException(
            f'Invalid geometry type: {geom_type} is not Polygon.')
    return geom


def geom_from_geojson(data: dict) -> dict:
    """Get GeoJSON geometry from GeoJSON.

    Parameters:
        data: GeoJSON geometry, Feature, or FeatureClass.

    Returns:
        GeoJSON geometry.

    Raises:
        GeoJSONException: If data is not valid GeoJSON geometry
    """
    if set(('coordinates', 'type')).issubset(set(data.keys())):
        # already a geom
        ret = data
    else:
        try:
            # feature
            ret = as_geom(data['geometry'])
        except KeyError:
            try:
                # featureclass
                features = data['features']
            except KeyError:
                raise GeoJSONException('Invalid GeoJSON: {data}')

            if len(features) > 1:
                raise MultipleFeaturesException(
                    'FeatureClass has multiple features. Only one feature '
                    'can be used to get geometry.')

            ret = as_geom(features[0])
    return ret


def validate_geom(data: dict):
    """Validate GeoJSON geometry.

    Parameters:
        data: GeoJSON geometry.

    Raises:
        GeoJSONException: If data is not a valid GeoJSON geometry.
    """
    if 'type' not in data:
        raise GeoJSONException(
            'Missing \'type\' key.')
    elif 'coordinates' not in data:
        raise GeoJSONException(
            'Missing \'coordinates\' key.')

    try:
        sgeom.shape(data)
    except ValueError as e:
        # invalid type or coordinates
        raise GeoJSONException(e)
    except TypeError:
        # wrong type
        raise GeoJSONException('Geometry coordinates do not fit type')
