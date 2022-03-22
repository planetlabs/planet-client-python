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


@pytest.fixture
def assert_geom_equal():
    def _tuple_to_list(obj):
        return json.loads(json.dumps(obj).replace(")", "]").replace("(", "["))

    def fcn(geom_1, geom_2):
        str_1 = _tuple_to_list(geom_1)
        str_2 = _tuple_to_list(geom_2)
        assert str_1 == str_2
    return fcn


def test_geom_from_geojson_success(
        geom_geojson, feature_geojson, featureclass_geojson,
        assert_geom_equal):
    ggeo = geojson.as_geom(geom_geojson)
    assert_geom_equal(ggeo, geom_geojson)

    fgeo = geojson.geom_from_geojson(feature_geojson)
    assert_geom_equal(fgeo, geom_geojson)

    fcgeo = geojson.geom_from_geojson(featureclass_geojson)
    assert_geom_equal(fcgeo, geom_geojson)


def test_geom_from_geojson_no_geometry(feature_geojson):
    feature_geojson.pop('geometry')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.geom_from_geojson(feature_geojson)


def test_geom_from_geojson_missing_coordinates(geom_geojson):
    geom_geojson.pop('coordinates')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.geom_from_geojson(geom_geojson)


def test_geom_from_geojson_missing_type(geom_geojson):
    geom_geojson.pop('type')
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.geom_from_geojson(geom_geojson)


def test_geom_from_geojson_multiple_features(featureclass_geojson):
    # duplicate the feature
    featureclass_geojson['features'] = 2 * featureclass_geojson['features']
    with pytest.raises(geojson.MultipleFeaturesException):
        _ = geojson.geom_from_geojson(featureclass_geojson)


def test_validate_geom_invalid_type(geom_geojson):
    geom_geojson['type'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.validate_geom(geom_geojson)


def test_validate_geom_wrong_type(geom_geojson):
    geom_geojson['type'] = 'point'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.validate_geom(geom_geojson)


def test_validate_geom_invalid_coordinates(geom_geojson):
    geom_geojson['coordinates'] = 'invalid'
    with pytest.raises(geojson.GeoJSONException):
        _ = geojson.validate_geom(geom_geojson)


def test_validate_geom_empty_coordinates(geom_geojson):
    geom_geojson['coordinates'] = []
    _ = geojson.validate_geom(geom_geojson)


def test_as_geom(geom_geojson):
    assert geojson.as_geom(geom_geojson) == geom_geojson


def test_as_polygon(geom_geojson):
    assert geojson.as_polygon(geom_geojson) == geom_geojson


def test_as_polygon_wrong_type(point_geom_geojson):
    with pytest.raises(geojson.WrongTypeException):
        _ = geojson.as_polygon(point_geom_geojson)
