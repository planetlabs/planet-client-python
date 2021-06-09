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
import json
import logging

import shapely.geometry as sgeom


LOGGER = logging.getLogger(__name__)


class GeoJSONException(Exception):
    '''invalid geojson'''
    pass


class WrongTypeException(GeoJSONException):
    '''wrong GeoJSON type'''
    pass


class Geometry():
    '''Manage and validate GeoJSON geometry description.'''
    def __init__(
        self,
        data: dict
    ):
        """
        Initialize GeoJSON.

        If data represents a GeoJSON FeatureClass, the geometry of the first
        Feature is used.

        Parameters:
            data: GeoJSON geometry, Feature, or FeatureClass.
        """
        self._data = self._geom_from_dict(data)
        self._type = self._geom_type(self._data)

    @classmethod
    def _geom_from_dict(
        cls,
        data: dict
    ):
        '''Extract the geometry description from GeoJSON.

        If data represents a FeatureClass, the geometry from the first feature
        is used.

        Parameters:
            data: GeoJSON geometry, Feature, or FeatureClass.

        Raises:
            GeoJSONException: If data is not valid GeoJSON geometry, Feature,
            or FeatureClass.
        '''
        if set(('coordinates', 'type')).issubset(set(data.keys())):
            # already a geom
            ret = data
        else:
            try:
                # feature
                ret = cls._geom_from_dict(data["geometry"])
            except KeyError:
                try:
                    # featureclass
                    features = data['features']
                except KeyError:
                    raise GeoJSONException('Invalid GeoJSON')

                ret = cls._geom_from_dict(features[0])
        return ret

    @staticmethod
    def _geom_type(data: dict):
        '''
        Parameters:
            data: GeoJSON geometry

        Raises:
            GeoJSONException: If data is not valid GeoJSON geometry, Feature,
            or FeatureClass.
            WrongTypeException: If geometry coordinates to not fit type.
        '''
        if 'type' not in data:
            raise GeoJSONException(
                'Missing \'type\' key.')
        elif 'coordinates' not in data:
            raise GeoJSONException(
                'Missing \'coordinates\' key.')

        try:
            # ugh, this changes the underlying data
            # notably coordinates as a list are converted to a tuple
            shape = sgeom.shape(data)
        except ValueError as e:
            # invalid type or coordinates
            raise GeoJSONException(e)
        except TypeError:
            # wrong type
            raise WrongTypeException('Geometry coordinates do not fit type')

        return shape.type

    def type_matches(self, other):
        return issubclass(self._type, other)

    def to_dict(self):
        return self._data

    def to_str(self):
        return json.dumps(self.to_dict())


class Polygon(Geometry):
    def __init__(
        self,
        data: dict
    ):
        """
        Initialize GeoJSON.

        If data represents a GeoJSON FeatureClass, the geometry of the first
        Feature is used.

        Parameters:
            data: Feature, FeatureClass, or geometry GeoJSON description.


        Raises:
            WrongTypeException: If data geometry type is not Polygon.
        """
        super().__init__(data)
        if self._type.lower() != 'polygon':
            raise WrongTypeException(
                f'Invalid geometry type: {self._type} is not Polygon.'
                )

    @classmethod
    def from_geometry(cls, geometry):
        return cls(geometry.to_dict())
