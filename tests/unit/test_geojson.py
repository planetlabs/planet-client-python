# Copyright 2021 Planet Labs, Inc.
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
import logging

import pytest

from planet import geojson

LOGGER = logging.getLogger(__name__)


def test_Geometry__init__success(geom_geojson):
    geo = geojson.Geometry(geom_geojson)
    assert geo.type == geom_geojson['type']


def test_Geometry__eq__(geom_geojson):
    geom_tuple = {
        "type": "Point",
        "coordinates": (-103.0078125, 40.713955826286046)
      }
    geom_list = {
        "type": "Point",
        "coordinates": [-103.0078125, 40.713955826286046]
      }

    assert geojson.Geometry(geom_tuple) == geojson.Geometry(geom_list)


def test_Geometry__init__missing_type(geom_geojson):
    geom_geojson.pop('type')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__invalid_type(geom_geojson):
    geom_geojson['type'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__wrong_type(geom_geojson):
    geom_geojson['type'] = 'point'
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__missing_coordinates(geom_geojson):
    geom_geojson.pop('coordinates')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__invalid_coordinates(geom_geojson):
    geom_geojson['coordinates'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__empty_coordinates(geom_geojson):
    geom_geojson['coordinates'] = []
    _ = geojson.Geometry(geom_geojson)


def test_Geometry__init__feature(geom_geojson, feature_geojson):
    assert geojson.Geometry(feature_geojson) == \
        geojson.Geometry(geom_geojson)


def test_Geometry__init__featureclass(geom_geojson, featureclass_geojson):
    assert geojson.Geometry(featureclass_geojson) == \
        geojson.Geometry(geom_geojson)


def test_Geometry__init__no_geometry(feature_geojson):
    feature_geojson.pop('geometry')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry(feature_geojson)


def test_Polygon__init__(geom_geojson):
    geom = geojson.Geometry(geom_geojson)

    # init from dict
    assert geojson.Polygon(geom_geojson) == geom

    # init from Geometry
    assert geojson.Polygon(geom) == geom


def test_Polygon_wrong_type(point_geom_geojson):
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.Polygon(point_geom_geojson)
