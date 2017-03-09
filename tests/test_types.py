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
from planet.scripts.types import _allowed_item_types
from planet.scripts.types import AssetType
from planet.scripts.types import GeomFilter
from planet.scripts.types import ItemType
from planet.scripts.types import Range
import pytest


def convert_asserter(t):
    def asserter(val, expected):
        assert set(t.convert(val, None, None)) == set(expected)
    return asserter


def test_item_type():
    check = convert_asserter(ItemType())

    check('all', _allowed_item_types)
    check('psscene', ['PSScene3Band', 'PSScene4Band'])
    check('Sentinel2L1C', ['Sentinel2L1C'])
    check('psscene,sent', ['PSScene3Band', 'PSScene4Band', 'Sentinel2L1C'])

    with pytest.raises(Exception) as e:
        ItemType().convert('x', None, None)
    assert 'invalid choice: x' in str(e.value)


def test_asset_type():
    check = convert_asserter(AssetType())
    check('visual*', ['visual', 'visual_xml'])
    check('*data_*', ['metadata_aux', 'metadata_txt'])
    check('analytic', ['analytic'])
    check('analytic,visual', ['analytic', 'visual'])

    with pytest.raises(Exception) as e:
        AssetType().convert('x', None, None)
    assert 'invalid choice: x' in str(e.value)


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
