# Copyright 2021 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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

from planet import geojson, exceptions

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


def test_geom_from_geojson_success(geom_geojson,
                                   feature_geojson,
                                   featurecollection_geojson,
                                   assert_geom_equal):
    ggeo = geojson.as_geom_or_ref(geom_geojson)
    assert_geom_equal(ggeo, geom_geojson)

    fgeo = geojson.geom_from_geojson(feature_geojson)
    assert_geom_equal(fgeo, geom_geojson)

    fcgeo = geojson.geom_from_geojson(featurecollection_geojson)
    assert_geom_equal(fcgeo, geom_geojson)


def test_geom_from_geojson_no_geometry(feature_geojson):
    feature_geojson.pop("geometry")
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.geom_from_geojson(feature_geojson)


def test_geom_from_geojson_missing_coordinates(geom_geojson):
    geom_geojson.pop("coordinates")
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.geom_from_geojson(geom_geojson)


def test_geom_from_geojson_missing_type(geom_geojson):
    geom_geojson.pop("type")
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.geom_from_geojson(geom_geojson)


def test_geom_from_geojson_multiple_features(featurecollection_geojson):
    # duplicate the feature
    featurecollection_geojson[
        "features"] = 2 * featurecollection_geojson["features"]
    with pytest.raises(geojson.GeoJSONError):
        _ = geojson.geom_from_geojson(featurecollection_geojson)


def test_validate_geom_as_geojson_invalid_type(geom_geojson):
    geom_geojson["type"] = "invalid"
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.validate_geom_as_geojson(geom_geojson)


def test_validate_geom_as_geojson_wrong_type(geom_geojson):
    geom_geojson["type"] = "point"
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.validate_geom_as_geojson(geom_geojson)


def test_validate_geom_as_geojson_invalid_coordinates(geom_geojson):
    geom_geojson["coordinates"] = "invalid"
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.validate_geom_as_geojson(geom_geojson)


def test_validate_geom_as_geojson_empty_coordinates(geom_geojson):
    geom_geojson["coordinates"] = []
    _ = geojson.validate_geom_as_geojson(geom_geojson)


def test_as_geojson(geom_geojson):
    assert geojson.as_geom_or_ref(geom_geojson) == geom_geojson


def test_as_polygon(geom_geojson):
    assert geojson.as_polygon(geom_geojson) == geom_geojson


def test_as_ref(geom_reference):
    assert geojson.as_ref(geom_reference) == geom_reference


def test_as_str_ref(str_geom_reference):
    geomify_ref = {
        "type": "ref",
        "content": str_geom_reference,
    }
    assert geojson.as_ref(str_geom_reference) == geomify_ref


def test_as_invalid_ref():
    with pytest.raises(exceptions.FeatureError):
        geojson.as_ref("some:nonesense/with/nothing")


def test_as_polygon_wrong_type(point_geom_geojson):
    with pytest.raises(exceptions.GeoJSONError):
        _ = geojson.as_polygon(point_geom_geojson)


def test_as_featurecollection_success(feature_geojson):
    feature2 = feature_geojson.copy()
    feature2["properties"] = {"foo": "bar"}
    values = [feature_geojson, feature2]
    res = geojson.as_featurecollection(values)

    expected = {"type": "FeatureCollection", "features": values}
    assert res == expected


def test__is_instance_of_success(feature_geojson):
    assert geojson._is_instance_of(feature_geojson, "Feature")

    feature2 = feature_geojson.copy()
    feature2["properties"] = {"foo": "bar"}
    assert geojson._is_instance_of(feature2, "Feature")


def test__is_instance_of_does_not_exist(feature_geojson):
    with pytest.raises(exceptions.GeoJSONError):
        geojson._is_instance_of(feature_geojson, "Foobar")
