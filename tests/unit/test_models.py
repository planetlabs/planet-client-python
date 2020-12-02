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
import io
import logging
from mock import MagicMock

import pytest

from planet.api import exceptions, models


LOGGER = logging.getLogger(__name__)

TEST_ITEM_KEY = 'testitem'
TEST_LINKS_KEY = 'testlinks'
TEST_NEXT_KEY = 'testnext'
NUM_ITEMS = 5


@pytest.fixture
def mocked_request():
    return models.Request('url', 'auth')


def mock_http_response(json, iter_content=None):
    m = MagicMock(name='http_response')
    m.headers = {}
    m.json.return_value = json
    m.iter_content = iter_content
    return m


def test_Request__raise_for_status():
    models.Response._raise_for_status(201, '')

    with pytest.raises(exceptions.TooManyRequests):
        models.Response._raise_for_status(429, '')

    with pytest.raises(exceptions.OverQuota):
        models.Response._raise_for_status(429, 'exceeded QUOTA dude')


def test_Body_write(tmpdir, mocked_request):
    chunks = ((str(i) * 16000).encode('utf-8') for i in range(10))

    body = models.Body(mocked_request, mock_http_response(
        json=None,
        iter_content=lambda chunk_size: chunks
    ))
    buf = io.BytesIO()
    body.write(buf)

    assert len(buf.getvalue()) == 160000


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
