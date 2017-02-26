# Copyright 2015 Planet Labs, Inc.
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
from datetime import datetime
import json
from planet.api import utils
from _common import read_fixture


def test_strp_lenient():
    for spec in [
        '2017-02-02T16:45:43.887484+00:00',
        '2017-02-02T16:45:43.887484+00',
        '2017-02-02T16:45:43.887484',
        '2017-02-02T16:45:43',
        '2017-02-02T16:45',
        '2017-02-02T16',
        '2017-02-02',
    ]:
        p = utils.strp_lenient(spec)
        assert datetime.strftime(p, utils._ISO_FMT).startswith(spec)


def test_geometry_from_json():
    # base case, no geometry
    assert None is utils.geometry_from_json({})
    # from an empty feature collection
    collection = {'type': 'FeatureCollection', 'features': []}
    assert None is utils.geometry_from_json(collection)

    # simple geometry, we're guessing by the type property w/ no further checks
    geom = {'type': 'Polygon'}
    assert geom == utils.geometry_from_json(geom)
    # from a feature
    feature = {'type': 'Feature', 'geometry': geom}
    assert geom == utils.geometry_from_json(feature)
    # from a feature collection
    collection = {'type': 'FeatureCollection', 'features': [feature]}
    assert geom == utils.geometry_from_json(collection)


def test_probably_wkt():
    # not wkt
    assert not utils.probably_wkt('')
    assert not utils.probably_wkt('{ geojson }')
    # it is wkt but we don't support it
    assert not utils.probably_wkt('POLYHEDRALSURFACE ()')
    assert not utils.probably_wkt('TRIANGLE((0 0 0,0 1 0,1 1 0,0 0 0))')

    # all valid wkt
    wkt = read_fixture('valid-wkt.txt').split('\n')
    assert len(wkt) > 0
    for valid in wkt:
        assert utils.probably_wkt(valid)


def test_probably_geojson():
    # nope
    assert utils.probably_geojson('') is None
    assert utils.probably_geojson('{}') is None
    assert utils.probably_geojson({}) is None
    assert utils.probably_geojson({'type': 'random'}) is None
    # yep
    assert utils.probably_geojson({'type': 'Point'}) == {'type': 'Point'}
    assert utils.probably_geojson('{"type": "Point"}') == {'type': 'Point'}
