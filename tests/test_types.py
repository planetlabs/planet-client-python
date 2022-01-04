# Copyright 2017 Planet Labs, Inc.
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
# limitations under the License

import json
import mock
from planet.scripts.item_asset_types import DEFAULT_ASSET_TYPES
from planet.scripts.item_asset_types import DEFAULT_ITEM_TYPES
from planet.scripts.types import AssetType
from planet.scripts.types import GeomFilter
from planet.scripts.types import ItemType
from planet.scripts.types import Range
import pytest


def convert_asserter(t):
    def asserter(val, expected):
        assert set(t.convert(val, None, None)) == set(expected)
    return asserter


@mock.patch('planet.scripts.types.get_item_types',
            new=mock.Mock(return_value=DEFAULT_ITEM_TYPES))
def test_item_type():
    check = convert_asserter(ItemType())

    check('all', DEFAULT_ITEM_TYPES)
    check('psscene*', ['PSScene', 'PSScene3Band', 'PSScene4Band'])
    check('Sentinel2L1C', ['Sentinel2L1C'])
    check('psscene*,sent*', [
        'PSScene', 'PSScene3Band', 'PSScene4Band', 'Sentinel1', 'Sentinel2L1C'
    ])

    with pytest.raises(Exception) as e:
        ItemType().convert('x', None, None)
    assert 'invalid choice: x' in str(e.value)


@mock.patch(
    "planet.scripts.types.get_asset_types",
    new=mock.Mock(return_value=DEFAULT_ASSET_TYPES),
)
@pytest.mark.parametrize(
    "pattern,type_list",
    [
        ("visual*", ["visual", "visual_xml"]),
        ("*data_*", ["metadata_aux", "metadata_txt"]),
        ("analytic", ["analytic"]),
        ("analytic,visual", ["analytic", "visual"]),
    ],
)
def test_asset_type_convert(pattern, type_list):
    """Patterns are correctly converted to a list of assert types."""
    assert sorted(AssetType()(pattern)) == sorted(type_list)


@mock.patch(
    "planet.scripts.types.get_asset_types",
    new=mock.Mock(return_value=DEFAULT_ASSET_TYPES),
)
@pytest.mark.parametrize("pattern", ["x", "foo?", "?visual", "visual?"])
def test_asset_type_convert_invalid(pattern):
    """Invalid patterns result in an exception."""
    with pytest.raises(Exception) as exc:
        AssetType()(pattern)
    assert "invalid choice:" in str(exc.value)


def test_geom_type():
    t = GeomFilter()
    geom = {"type": "Point", "coordinates": [1, 2]}
    feature = {"type": "Feature", "geometry": geom}
    coll = {"type": "FeatureCollection", "features": [feature]}
    expect = [{
        'config': {
            u'type': u'Point',
            u'coordinates': [1, 2]
        },
        'field_name': 'geometry',
        'type': 'GeometryFilter'
    }]
    expect == t.convert(json.dumps(geom), None, None)
    expect == t.convert(json.dumps(feature), None, None)
    expect == t.convert(json.dumps(coll), None, None)
    with pytest.raises(Exception) as e:
        t.convert('{"type": "Point"}', None, None)
    assert 'unable to find geometry in input' in str(e.value)


def test_range_type():
    t = Range()

    expect = {'config': {'gt': 42.0}, 'field_name': 'x', 'type': 'RangeFilter'}
    assert expect == t.convert('x gt 42'.split(' '), None, None)
    with pytest.raises(Exception) as e:
        t.convert('x gt a'.split(' '), None, None)
    assert 'invalid value for range: "a", must be number' in str(e.value)
