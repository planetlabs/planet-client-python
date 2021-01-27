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
import logging
import math
from mock import MagicMock
import os
from pathlib import Path

import pytest

from planet.api import exceptions, models

TEST_ITEM_KEY = 'testitem'
TEST_LINKS_KEY = 'testlinks'
TEST_NEXT_KEY = 'testnext'
NUM_ITEMS = 5

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


# def test_Request__raise_for_status():
#     models.Response._raise_for_status(201, mock_http_response(text=''))
#
#     with pytest.raises(exceptions.TooManyRequests):
#         models.Response._raise_for_status(429, mock_http_response(text=''))
#
#     with pytest.raises(exceptions.OverQuota):
#         msg = 'exceeded QUOTA dude'
#         models.Response._raise_for_status(429,  mock_http_response(text=msg))


# def test_Body_write(tmpdir, mocked_request):
#     chunks = ((str(i) * 16000).encode('utf-8') for i in range(10))
#
#     body = models.Body(mocked_request, mock_http_response(
#         iter_content=lambda chunk_size: chunks
#     ))
#     buf = io.BytesIO()
#     body.write(buf)
#
#     assert len(buf.getvalue()) == 160000


@pytest.mark.asyncio
async def test_StreamingBody_write_img(tmpdir, mocked_request, open_test_img):
    async def _aiter_bytes():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        LOGGER.warning('called')
        for i in range(math.ceil(len(v)/(chunksize))):
            yield v[i*chunksize:min((i+1)*chunksize, len(v))]

    r = MagicMock(name='response')
    hr = MagicMock(name='http_response')
    hr.aiter_bytes = _aiter_bytes
    hr.num_bytes_downloaded = 0
    hr.response.headers['Content-Length'] = 527
    r.http_response = hr
    body = models.StreamingBody(r)

    filename = Path(str(tmpdir)) / 'test.tif'
    await body.write(filename, progress_bar=False)

    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 527


# def test_Body_write_to_file_callback(mocked_request, tmpdir):
#     class Tracker(object):
#         def __init__(self):
#             self.calls = []
#
#         def get_callback(self):
#             def register_call(start=None, wrote=None, total=None, finish=None,
#                               skip=None):
#                 if start is not None:
#                     self.calls.append('start')
#                 if wrote is not None and total is not None:
#                     self.calls.append('wrote, total')
#                 if finish is not None:
#                     self.calls.append('finish')
#                 if skip is not None:
#                     self.calls.append('skip')
#             return register_call
#
#     chunks = ((str(i) * 16000).encode('utf-8') for i in range(2))
#
#     body = models.Body(mocked_request, mock_http_response(
#         iter_content=lambda chunk_size: chunks
#     ))
#
#     test = Tracker()
#     filename = Path(str(tmpdir)) / 'test.tif'
#     body.write_to_file(filename=filename, callback=test.get_callback())
#
#     assert test.calls == ['start', 'wrote, total', 'wrote, total', 'finish']
#
#     # should skip writing the file because a file with that filename already
#     # exists
#     test.calls = []
#     body.write_to_file(filename=filename, callback=test.get_callback(),
#                        overwrite=False)
#     assert test.calls == ['skip']


# class TestPaged(models.Paged):
#     def _get_item_key(self):
#         return TEST_ITEM_KEY
#
#     def _get_links_key(self):
#         return TEST_LINKS_KEY
#
#     def _get_next_key(self):
#         return TEST_NEXT_KEY
#
#
# @pytest.fixture
# def test_paged():
#     request = models.Request('url', 'auth')
#
#     # make 5 pages with 5 items on each page
#     pages = _make_pages(5, NUM_ITEMS)
#     http_response = mock_http_response(json=next(pages))
#
#     # initialize the paged object with the first page
#     paged = TestPaged(request, http_response)
#
#     # the remaining 4 get used here
#     ps = MagicMock(name='PlanetSession')
#     ps.request.side_effect = (
#         mock_http_response(json=p) for p in pages
#     )
#     # mimic dispatcher.response
#     return paged
#
#
# def _make_pages(cnt, num):
#     '''generator of 'cnt' pages containing 'num' content'''
#     start = 0
#     for p in range(num):
#         nxt = 'page %d' % (p + 1,) if p + 1 < num else None
#         start, page = _make_test_page(cnt, start, nxt)
#         yield page
#
#
# def _make_test_page(cnt, start, nxt):
#     '''fake paged content'''
#     envelope = {
#         TEST_LINKS_KEY: {
#             TEST_NEXT_KEY: nxt
#         },
#         TEST_ITEM_KEY: [{
#             'testitementry': start + t
#         } for t in range(cnt)]
#     }
#     return start + cnt, envelope
#

# def test_Paged_next(test_paged):
#     pages = list(test_paged.iter(2))
#     assert 2 == len(pages)
#     assert NUM_ITEMS == len(pages[0].get()[TEST_ITEM_KEY])
#     assert NUM_ITEMS == len(pages[1].get()[TEST_ITEM_KEY])
#
#
# def test_Paged_iter(test_paged):
#     pages = list(test_paged.iter(2))
#     assert 2 == len(pages)
#     assert NUM_ITEMS == len(pages[0].get()[TEST_ITEM_KEY])
#     assert NUM_ITEMS == len(pages[1].get()[TEST_ITEM_KEY])
#
#
# @pytest.mark.skip(reason='not implemented')
# def test_Paged_items_iter():
#     pass
#
#
# @pytest.mark.skip(reason='not implemented')
# def test_Paged_json_encode():
#     pass
