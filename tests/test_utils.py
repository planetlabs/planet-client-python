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
from mock import Mock
import pytest
from datetime import datetime
import re
from planet.api import utils
from planet.api import exceptions
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
        assert p is not None, spec + " failed"
        assert datetime.strftime(p, utils._ISO_FMT).startswith(spec)

    withz = '2017-02-02T16:45:43Z'
    assert utils.strp_lenient(withz) == utils.strp_lenient(withz[:-1])


def test_geometry_from_json():
    # base case, no geometry
    assert None is utils.geometry_from_json({})
    # from an empty feature collection
    collection = {'type': 'FeatureCollection', 'features': []}
    assert None is utils.geometry_from_json(collection)

    # simple geometry, we're guessing by the type property and presence of
    # the coordinates property
    geom = {'type': 'Polygon', 'coordinates': [1, 2]}
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


def test_check_status():
    r = Mock()
    r.status_code = 429
    r.text = ''
    with pytest.raises(exceptions.TooManyRequests):
        utils.check_status(r)
    r.text = 'exceeded QUOTA dude'
    with pytest.raises(exceptions.OverQuota):
        utils.check_status(r)


def test_write_to_file(tmpdir):
    body = Mock()
    body.name = 'foobar'
    body.write.return_value = None
    utils.write_to_file(str(tmpdir))(body)
    path, callback = body.write.call_args[0]
    expected = tmpdir.join(body.name)
    assert str(expected) == path
    assert callback is None

    expected.write('')
    callback = Mock()
    callback.return_value = None
    utils.write_to_file(str(tmpdir), overwrite=False)(body)
    utils.write_to_file(str(tmpdir), callback=callback, overwrite=False)(body)
    assert body.write.call_count == 1
    assert callback.call_args[1]['skip'] == body


@pytest.mark.parametrize('headers,expected', [
    ({
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
        'content-disposition': 'attachment; filename="open_california.tif"'
    }, 'open_california.tif'),
    ({
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256'
    }, None),
    ({}, None)
])
def test_get_filename_from_headers(headers, expected):
    assert utils.get_filename_from_headers(headers) == expected


@pytest.mark.parametrize('url,expected', [
    ('https://planet.com/', None),
    ('https://planet.com/path/to/', None),
    ('https://planet.com/path/to/example.tif', 'example.tif'),
    ('https://planet.com/path/to/example.tif?foo=f6f1&bar=baz', 'example.tif'),
    ('https://planet.com/path/to/example.tif?foo=f6f1#quux', 'example.tif'),
])
def test_get_filename_from_url(url, expected):
    assert utils.get_filename_from_url(url) == expected


@pytest.mark.parametrize('content_type,check', [
    (None, lambda x: re.match(r'^planet-[a-z0-9]{8}$', x, re.I) is not None),
    ('image/tiff', lambda x: x.endswith(('.tif', '.tiff'))),
])
def test_get_random_filename(content_type, check):
    assert check(utils.get_random_filename(content_type))
