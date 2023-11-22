# Copyright 2020 Planet Labs, Inc.
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
from datetime import datetime, timedelta, timezone
import logging
import pytest

from planet import data_filter, exceptions

LOGGER = logging.getLogger(__name__)


def test_and_filter():
    f1 = {'type': 'testf1'}
    f2 = {'type': 'testf2'}
    res = data_filter.and_filter([f1, f2])
    expected = {'type': 'AndFilter', 'config': [f1, f2]}
    assert res == expected


def test_or_filter():
    f1 = {'type': 'testf1'}
    f2 = {'type': 'testf2'}
    res = data_filter.or_filter([f1, f2])
    expected = {'type': 'OrFilter', 'config': [f1, f2]}
    assert res == expected


def test_not_filter():
    f1 = {'type': 'testf1'}
    res = data_filter.not_filter(f1)
    expected = {'type': 'NotFilter', 'config': f1}
    assert res == expected


def test__range_filter_success():

    def _test_callback(x):
        return x + 'a'

    res = data_filter._range_filter('testfilter',
                                    'testfield',
                                    gt='a',
                                    gte=None,
                                    lt='b',
                                    lte='c',
                                    callback=_test_callback)
    expected = {
        'type': 'testfilter',
        'field_name': 'testfield',
        'config': {
            'gt': 'aa', 'lt': 'ba', 'lte': 'ca'
        }
    }
    assert expected == res


def test__range_filter_nocallback():
    res = data_filter._range_filter('testfilter',
                                    'testfield',
                                    gt='a',
                                    gte=None,
                                    lt='b',
                                    lte='c')
    expected = {
        'type': 'testfilter',
        'field_name': 'testfield',
        'config': {
            'gt': 'a', 'lt': 'b', 'lte': 'c'
        }
    }
    assert expected == res


def test__range_filter_no_conditionals():

    def _test_callback(x):  # pragma: no cover
        return x + 'a'

    with pytest.raises(exceptions.PlanetError):
        data_filter._range_filter('testfilter',
                                  'testfield',
                                  gt=None,
                                  gte=None,
                                  lt=None,
                                  lte=None,
                                  callback=_test_callback)


@pytest.mark.parametrize(
    "dtime,expected",
    [(datetime(2022, 5, 1, 1, 0, 0, 1), '2022-05-01T01:00:00.000001Z'),
     (datetime(2022, 5, 1, 1, 0, 1), '2022-05-01T01:00:01Z'),
     (datetime(2022, 6, 1, 1, 1), '2022-06-01T01:01:00Z'),
     (datetime(2022, 6, 1, 1), '2022-06-01T01:00:00Z'),
     (datetime(2022, 6, 1, 1, tzinfo=timezone(timedelta(hours=1))),
      '2022-06-01T01:00:00+01:00'),
     (datetime(2022, 6, 1, 1, tzinfo=timezone(timedelta(0))),
      '2022-06-01T01:00:00+00:00')])
def test__datetime_to_rfc3339_basic(dtime, expected):
    assert data_filter._datetime_to_rfc3339(dtime) == expected


def test_date_range_filter_success():
    res = data_filter.date_range_filter('testfield',
                                        gt=datetime(2022, 6, 1, 1),
                                        lt=datetime(2022, 7, 1, 1))
    expected = {
        'type': 'DateRangeFilter',
        'field_name': 'testfield',
        'config': {
            'gt': '2022-06-01T01:00:00Z', 'lt': '2022-07-01T01:00:00Z'
        }
    }
    assert res == expected


def test_range_filter_noconditionals():
    with pytest.raises(exceptions.PlanetError):
        data_filter.range_filter('acquired')


def test_range_filter_success():
    res = data_filter.range_filter('testfield', gt=0.1, lt=0.9)
    expected = {
        'type': 'RangeFilter',
        'field_name': 'testfield',
        'config': {
            'gt': 0.1, 'lt': 0.9
        }
    }
    assert res == expected


def test_date_range_filter_noconditionals():
    with pytest.raises(exceptions.PlanetError):
        data_filter.date_range_filter('acquired')


def test_update_filter_success():
    res = data_filter.update_filter('testfield', gt=datetime(2022, 6, 1, 1))
    expected = {
        'type': 'UpdateFilter',
        'field_name': 'testfield',
        'config': {
            'gt': '2022-06-01T01:00:00Z'
        }
    }
    assert res == expected


def test_update_filter_noconditionals():
    with pytest.raises(exceptions.PlanetError):
        data_filter.update_filter('acquired')


@pytest.mark.parametrize("geom_fixture",
                         [('geom_geojson'), ('feature_geojson'),
                          ('featurecollection_geojson')])
def test_geometry_filter(geom_fixture, request, geom_geojson):
    geom = request.getfixturevalue(geom_fixture)
    res = data_filter.geometry_filter(geom)
    expected = {
        'type': 'GeometryFilter',
        'field_name': 'geometry',
        'config': geom_geojson
    }
    assert res == expected


def test_number_in_filter():
    res = data_filter.number_in_filter('testfield', [3, 3])
    expected = {
        'type': 'NumberInFilter', 'field_name': 'testfield', 'config': [3, 3]
    }
    assert res == expected


def test_string_in_filter():
    res = data_filter.string_in_filter('testfield', ['three', 'three'])
    expected = {
        'type': 'StringInFilter',
        'field_name': 'testfield',
        'config': ['three', 'three']
    }
    assert res == expected


def test_asset_filter():
    res = data_filter.asset_filter(['asset1', 'asset2'])
    expected = {'type': 'AssetFilter', 'config': ['asset1', 'asset2']}
    assert res == expected


def test_permission_filter():
    res = data_filter.permission_filter()
    expected = {'type': 'PermissionFilter', 'config': ['assets:download']}
    assert res == expected


def test_std_quality_filter():
    res = data_filter.std_quality_filter()
    expected = {
        'type': 'StringInFilter',
        'field_name': 'quality_category',
        'config': ['standard']
    }
    assert res == expected
