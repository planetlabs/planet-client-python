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
# limitations under the License.
# import io
import copy
import logging
import math
from unittest.mock import MagicMock
import os
from pathlib import Path
import re

from httpx import URL
import pytest

from planet.api import models


LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mocked_request():
    return models.Request('url', 'auth')


def mock_http_response(json=None, iter_content=None, text=None):
    m = MagicMock(name='http_response')
    m.headers = {}
    m.json.return_value = json or {}
    m.aiter_content = iter_content
    m.text = text or ''
    return m


def test_StreamingBody_name():
    r = MagicMock(name='response')
    r.request.url = URL('https://planet.com/path/to/example.tif?foo=f6f1')
    hr = MagicMock(name='http_response')
    hr.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
        'content-disposition': 'attachment; filename="open_california.tif"'
    }
    r.http_response = hr
    body = models.StreamingBody(r)

    assert body.name == 'open_california.tif'

    r = MagicMock(name='response')
    r.request.url = URL('https://planet.com/path/to/example.tif?foo=f6f1')
    hr = MagicMock(name='http_response')
    hr.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
    }
    r.http_response = hr
    body = models.StreamingBody(r)

    assert body.name == 'example.tif'

    r = MagicMock(name='response')
    r.request.url = URL('https://planet.com/path/to/noname/')
    hr = MagicMock(name='http_response')
    hr.headers = {
        'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
        'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
        'accept-ranges': 'bytes',
        'content-type': 'image/tiff',
        'content-length': '57350256',
    }
    r.http_response = hr
    body = models.StreamingBody(r)

    assert body.name.startswith('planet-')
    assert body.name.endswith('.tiff')


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
def test__get_filename_from_headers(headers, expected):
    assert models._get_filename_from_headers(headers) == expected


@pytest.mark.parametrize('url,expected', [
    (URL('https://planet.com/'), None),
    (URL('https://planet.com/path/to/'), None),
    (URL('https://planet.com/path/to/example.tif'), 'example.tif'),
    (URL('https://planet.com/path/to/example.tif?foo=f6f1&bar=baz'),
     'example.tif'),
    (URL('https://planet.com/path/to/example.tif?foo=f6f1#quux'),
     'example.tif'),
])
def test__get_filename_from_url(url, expected):
    assert models._get_filename_from_url(url) == expected


@pytest.mark.parametrize('content_type,check', [
    (None, lambda x: re.match(r'^planet-[a-z0-9]{8}$', x, re.I) is not None),
    ('image/tiff', lambda x: x.endswith(('.tif', '.tiff'))),
])
def test__get_random_filename(content_type, check):
    assert check(models._get_random_filename(content_type))


@pytest.mark.asyncio
async def test_StreamingBody_write_img(tmpdir, mocked_request, open_test_img):
    async def _aiter_bytes():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v)/(chunksize))):
            yield v[i*chunksize:min((i+1)*chunksize, len(v))]

    r = MagicMock(name='response')
    hr = MagicMock(name='http_response')
    hr.aiter_bytes = _aiter_bytes
    hr.num_bytes_downloaded = 0
    hr.headers['Content-Length'] = 527
    r.http_response = hr
    body = models.StreamingBody(r)

    filename = Path(str(tmpdir)) / 'test.tif'
    await body.write(filename, progress_bar=False)

    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 527


@pytest.fixture
def get_pages():
    p1 = {'links': {'next': 'blah'},
          'items': [1, 2]}
    p2 = {'links': {},
          'items': [3, 4]}
    responses = [
        mock_http_response(json=p1),
        mock_http_response(json=p2)
    ]

    async def do_get(req):
        return responses.pop(0)

    return do_get


@pytest.mark.asyncio
async def test_Paged_iterator(get_pages):
    req = MagicMock()
    paged = models.Paged(req, get_pages)
    assert [1, 2, 3, 4] == [i async for i in paged]


@pytest.mark.asyncio
async def test_Paged_limit(get_pages):
    req = MagicMock()
    paged = models.Paged(req, get_pages, limit=3)
    assert [1, 2, 3] == [i async for i in paged]


@pytest.fixture
def get_orders_pages(orders_page):
    page2 = copy.deepcopy(orders_page)
    del page2['_links']['next']
    responses = [
        mock_http_response(json=orders_page),
        mock_http_response(json=page2)
    ]

    async def do_get(req):
        return responses.pop(0)

    return do_get


@pytest.mark.asyncio
async def test_Orders(get_orders_pages):
    req = MagicMock()
    orders = models.Orders(req, get_orders_pages)
    expected_ids = [
        'f05b1ed7-11f0-43da-960c-a624f7c355c8',
        '8d4799c4-5291-40c0-a7f5-adb9a974455d',
        'f05b1ed7-11f0-43da-960c-a624f7c355c8',
        '8d4799c4-5291-40c0-a7f5-adb9a974455d'
    ]
    assert expected_ids == [o.id async for o in orders]


def test_Order_results(order_description):
    order = models.Order(order_description)
    assert len(order.results) == 3


def test_Order_locations(order_description):
    order = models.Order(order_description)
    expected_locations = ['location1', 'location2', 'location3']
    assert order.locations == expected_locations
