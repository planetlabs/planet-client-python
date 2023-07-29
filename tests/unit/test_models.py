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
from unittest.mock import MagicMock

import httpx
import pytest

from planet import models
from planet.exceptions import PagingError

LOGGER = logging.getLogger(__name__)

NO_NAME_HEADERS = {
    'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    'accept-ranges': 'bytes',
    'Content-Type': 'image/tiff',
    'Content-Length': '57350256'
}
OPEN_CALIFORNIA_HEADERS = httpx.Headers({
    'date':
    'Thu, 14 Feb 2019 16:13:26 GMT',
    'last-modified':
    'Wed, 22 Nov 2017 17:22:31 GMT',
    'accept-ranges':
    'bytes',
    'Content-Type':
    'image/tiff',
    'Content-Length':
    '57350256',
    'Content-Disposition':
    'attachment; filename="open_california.tif"'
})


def test_Response_filename():
    r = MagicMock(name='response')
    r.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    r.headers = OPEN_CALIFORNIA_HEADERS

    assert models.Response(r).filename == 'open_california.tif'


def test__get_filename_from_response():
    r = MagicMock(name='response')
    r.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    r.headers = OPEN_CALIFORNIA_HEADERS
    assert models._get_filename_from_response(r) == 'open_california.tif'


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
