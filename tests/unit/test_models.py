# Copyright 2017 Planet Labs, Inc.
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
import logging
import math
from unittest.mock import MagicMock
import os
from pathlib import Path
import re

import pytest

from planet import models
from planet.exceptions import PagingError

LOGGER = logging.getLogger(__name__)


def test_StreamingBody_name_filename():
    r = MagicMock(name='response')
    r.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    r.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
        'content-disposition': 'attachment; filename="open_california.tif"'
    }
    body = models.StreamingBody(r)
    assert body.name == 'open_california.tif'


def test_StreamingBody_name_url():
    r = MagicMock(name='response')
    r.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    r.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
    }
    body = models.StreamingBody(r)

    assert body.name == 'example.tif'


def test_StreamingBody_name_content():
    r = MagicMock(name='response')
    r.url = 'https://planet.com/path/to/noname/'
    r.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
    }
    body = models.StreamingBody(r)

    assert body.name.startswith('planet-')
    assert (body.name.endswith('.tiff') or body.name.endswith('.tif'))


NO_NAME_HEADERS = {
    'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    'accept-ranges': 'bytes',
    'content-type': 'image/tiff',
    'content-length': '57350256'
}
OPEN_CALIFORNIA_HEADERS = {
    'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    'accept-ranges': 'bytes',
    'content-type': 'image/tiff',
    'content-length': '57350256',
    'content-disposition': 'attachment; filename="open_california.tif"'
}


@pytest.mark.parametrize('headers,expected',
                         [(OPEN_CALIFORNIA_HEADERS, 'open_california.tif'),
                          (NO_NAME_HEADERS, None),
                          ({}, None)])  # yapf: disable
def test__get_filename_from_headers(headers, expected):
    assert models._get_filename_from_headers(headers) == expected


@pytest.mark.parametrize(
    'url,expected',
    [
        ('https://planet.com/', None),
        ('https://planet.com/path/to/', None),
        ('https://planet.com/path/to/example.tif', 'example.tif'),
        ('https://planet.com/path/to/example.tif?foo=f6f1&bar=baz',
         'example.tif'),
        ('https://planet.com/path/to/example.tif?foo=f6f1#quux',
         'example.tif'),
    ])
def test__get_filename_from_url(url, expected):
    assert models._get_filename_from_url(url) == expected


@pytest.mark.parametrize(
    'content_type,check',
    [
        (None,
         lambda x: re.match(r'^planet-[a-z0-9]{8}$', x, re.I) is not None),
        ('image/tiff', lambda x: x.endswith(('.tif', '.tiff'))),
    ])
def test__get_random_filename(content_type, check):
    assert check(models._get_random_filename(content_type))


@pytest.mark.anyio
async def test_StreamingBody_write_img(tmpdir, open_test_img):

    async def _aiter_bytes():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v) / (chunksize))):
            yield v[i * chunksize:min((i + 1) * chunksize, len(v))]

    r = MagicMock(name='response')
    r.aiter_bytes = _aiter_bytes
    r.num_bytes_downloaded = 0
    r.headers['Content-Length'] = 527
    body = models.StreamingBody(r)

    filename = Path(tmpdir) / 'test.tif'
    await body.write(filename, progress_bar=False)

    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 527


@pytest.mark.anyio
async def test_Paged_iterator():
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        resp = MagicMock(name='response')
        resp.json = lambda: {'_links': {}, 'items': [3, 4]}
        return resp

    paged = models.Paged(resp, get_response)
    assert [1, 2, 3, 4] == [i async for i in paged]


@pytest.mark.anyio
@pytest.mark.parametrize('limit, expected', [(0, [1, 2, 3, 4]), (1, [1])])
async def test_Paged_limit(limit, expected):
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        resp = MagicMock(name='response')
        resp.json = lambda: {'_links': {}, 'items': [3, 4]}
        return resp

    paged = models.Paged(resp, get_response, limit=limit)
    assert [i async for i in paged] == expected


@pytest.mark.anyio
async def test_Paged_break_page_cycle():
    """Check that we break out of a page cycle."""
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        return resp

    paged = models.Paged(resp, get_response, limit=None)

    with pytest.raises(PagingError):
        [item async for item in paged]
