# Copyright 2021 Planet Labs, Inc.
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
"""Functionality for interacting with GeoJSON and planet references."""
import json
import logging
import typing

import geojson as gj
from jsonschema import Draft7Validator
from .constants import DATA_DIR
from .exceptions import GeoJSONError, FeatureError

GEOJSON_TYPES = ["Feature"]

LOGGER = logging.getLogger(__name__)


def as_geom_or_ref(data) -> dict:
    """Extract the geometry from GeoJSON and validate.

    Parameters:
        data: GeoJSON geometry, Feature, or FeatureCollection.

    Returns:
        GeoJSON geometry.

    Raises:
        GeoJSONError: If data is not valid GeoJSON geometry, Feature,
            or FeatureCollection or if more than one Feature is in a
            FeatureCollection.
    """
    if isinstance(data, str):
        return as_ref(data)
    geom_type = data['type']
    if geom_type == 'ref':
        return as_ref(data)
    else:
        geom = geom_from_geojson(data)
        validate_geom_as_geojson(geom)
        return geom


def validate_ref(uri) -> bool:
    if uri is None:
        raise FeatureError("Expected str, not None")
    parts = uri.split("/", 4)
    if parts[0] != "pl:features":
        raise FeatureError("Expected scheme pl:features")
    path = parts[1:]
    if len(path) < 2:
        raise FeatureError("Expceted dataset/collection path")
    return True


def convert_ref_to_dict(data: str) -> dict:
    """ Ensure geom reference is in the expected format
        Then convert it into a geometry block

    Parameters:
        data: str, a feature reference
    Returns:
        GeoJSON geometry reference
    """
    if validate_ref(data):
        geom = {
            "type": "ref",
            "content": data,
        }
        return geom
    return dict()


def as_ref(data) -> dict:
    if isinstance(data, str):
        data = convert_ref_to_dict(data)
    if isinstance(data, dict):
        geom_type = data['type']
        if geom_type.lower() != 'ref':
            raise FeatureError(
                f'Invalid geometry reference: {geom_type} is not a reference (the type should be "ref").'
            )
        if "content" not in data:
            raise FeatureError(
                'Invalid geometry reference: Missing content block that contains the reference.'
            )
    return data


def as_polygon(data: dict) -> dict:
    geom = as_geom_or_ref(data)
    geom_type = geom['type']
    if geom_type.lower() != 'polygon':
        raise GeoJSONError(
            f'Invalid geometry type: {geom_type} is not Polygon.')
    return geom


def geom_from_geojson(data: dict) -> dict:
    """Get GeoJSON geometry from GeoJSON.

    Parameters:
        data: GeoJSON geometry, Feature, or FeatureCollection.

    Returns:
        GeoJSON geometry.

    Raises:
        planet.exceptions.GeoJSONError: If data is not valid GeoJSON
        geometry or contains multiple features.
    """
    if set(('coordinates', 'type')).issubset(set(data.keys())):
        # already a geom
        ret = data
    else:
        try:
            # feature
            ret = as_geom_or_ref(data['geometry'])
        except KeyError:
            try:
                # FeatureCollection
                features = data['features']
            except KeyError:
                raise GeoJSONError(f'Invalid GeoJSON: {data}')

            if len(features) > 1:
                raise GeoJSONError(
                    'FeatureCollection has multiple features. Only one feature'
                    ' can be used to get geometry.')

            ret = as_geom_or_ref(features[0])
    return ret


def validate_geom_as_geojson(data: dict):
    """Validate GeoJSON geometry.

    Parameters:
        data: GeoJSON geometry.

    Raises:
        planet.exceptions.GeoJSONError: If data is not a valid GeoJSON
        geometry.
    Returns:
        GeoJSON
    """
    data = geom_from_geojson(data)
    if 'type' not in data:
        raise GeoJSONError('Missing "type" key.')
    if 'coordinates' not in data:
        raise GeoJSONError('Missing "coordinates" key.')

    try:
        cls = getattr(gj, data['type'])
        obj = cls(data['coordinates'])
        if not obj.is_valid:
            raise GeoJSONError(obj.errors())
    except AttributeError as err:
        raise GeoJSONError('Not a GeoJSON geometry type') from err
    except ValueError as err:
        raise GeoJSONError('Not a GeoJSON coordinate value') from err

    return data


def as_featurecollection(features: typing.List[dict]) -> dict:
    """Combine the features in a FeatureCollection.

    Parameters:
        features: GeoJSON Feature objects to combine.

    Raises:
        planet.exceptions.GeoJSONError: If any features are not valid
        GeoJSON Feature objects.
    """

    def _check_all_features(obj):
        for f in obj:
            if not _is_instance_of(f, 'Feature'):
                raise GeoJSONError(f'{f} is not a valid GeoJSON Feature ' +
                                   'object.')

    _check_all_features(features)
    return {'type': 'FeatureCollection', 'features': features}


def _is_instance_of(obj: dict, geojson_type: str) -> bool:
    """Determine if an object is a valid instance of a given GeoJSON type.

    Right now this is only used with the Feature GeoJSON type but this will
    be expanded.

    Parameters:
        obj: Input to check
        geojson_type: Name of geojson type to check


    Returns:
        Indication that the object is a valid instance of specified GeoJSON
        type.

    Raises:
        planet.exceptions.GeoJSONError: If geojson_type does not match a
        supported GeoJSON type.
    """
    try:
        schema_name = next(t + '.json' for t in GEOJSON_TYPES
                           if t.lower() == geojson_type.lower())
    except StopIteration:
        raise GeoJSONError(f'Specified geojson_type ({geojson_type}) does '
                           'not match a supported GeoJSON type.')

    filename = DATA_DIR / schema_name
    with open(filename, 'r') as src:
        schema = json.load(src)

    return Draft7Validator(schema).is_valid(obj)
