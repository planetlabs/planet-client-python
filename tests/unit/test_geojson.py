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
import json
import logging

import pytest

from planet import geojson

LOGGER = logging.getLogger(__name__)


def assert_geom_eq(g1, g2):
    g = json.loads(json.dumps(g1).replace(")", "]").replace("(", "["))
    assert g == g2


def test_Geometry__geom_type_success(geom_geojson):
    gtype = geojson.Geometry._geom_type(geom_geojson)
    assert gtype == geom_geojson['type']


def test_Geometry__geom_type_missing_type(geom_geojson):
    geom_geojson.pop('type')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_type_invalid_type(geom_geojson):
    geom_geojson['type'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_type_wrong_type(geom_geojson):
    geom_geojson['type'] = 'point'
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_type_missing_coordinates(geom_geojson):
    geom_geojson.pop('coordinates')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_type_invalid_coordinates(geom_geojson):
    geom_geojson['coordinates'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_type_empty_coordinates(geom_geojson):
    geom_geojson['coordinates'] = []
    _ = geojson.Geometry._geom_type(geom_geojson)


def test_Geometry__geom_from_dict_success(
        feature_geojson, featureclass_geojson, geom_geojson):
    geom = geojson.Geometry._geom_from_dict(geom_geojson)
    assert_geom_eq(geom, geom_geojson)

    f_geom = geojson.Geometry._geom_from_dict(feature_geojson)
    assert_geom_eq(f_geom, geom_geojson)

    fc_geom = geojson.Geometry._geom_from_dict(featureclass_geojson)
    assert_geom_eq(fc_geom, geom_geojson)


def test_Geometry__geom_from_dict_no_geometry(feature_geojson):
    feature_geojson.pop('geometry')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.Geometry._geom_from_dict(feature_geojson)


def test_Geometry__init__(geom_geojson):
    geo = geojson.Geometry(geom_geojson)
    assert_geom_eq(geo.to_dict(), geom_geojson)


def test_Polygon__init__(geom_geojson):
    geo = geojson.Polygon(geom_geojson)
    assert_geom_eq(geo.to_dict(), geom_geojson)


def test_Polygon_wrong_type(point_geom_geojson):
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.Polygon(point_geom_geojson)


def test_Polygon_from_Geometry(geom_geojson):
    geo = geojson.Geometry(geom_geojson)
    _ = geojson.Polygon.from_geometry(geo)


def test_Polygon_from_Geometry_wrong_type(point_geom_geojson):
    geo = geojson.Geometry(point_geom_geojson)
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.Polygon.from_geometry(geo)
