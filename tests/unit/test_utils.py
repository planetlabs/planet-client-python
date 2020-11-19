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
import pytest
import re
from planet.api import utils


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
