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
import json
import pytest
from planet.api.models import Features, Paged, Request, Response, WFS3Features
from mock import MagicMock
# try:
#     from StringIO import StringIO as Buffy
# except ImportError:
#     from io import BytesIO as Buffy


def mock_http_response(json, iter_content=None):
    m = MagicMock(name='http_response')
    m.headers = {}
    m.json.return_value = json
    m.iter_content = iter_content
    return m


def make_page(cnt, start, key, next, af):
    '''fake paged content'''
    if af:
        envelope = {
            'links': [{
                'href': next,
                'rel': 'next',
                'title': 'NEXT'
            }],
            key: [{
                'thingee': start + t
            } for t in range(cnt)]
        }
    else:
        envelope = {
            '_links': {
                '_next': next
            },
            key: [{
                'thingee': start + t
            } for t in range(cnt)]
        }
    return start + cnt, envelope


def make_pages(cnt, num, key, af):
    '''generator of 'cnt' pages containing 'num' content'''
    start = 0
    for p in range(num):
        next = 'page %d' % (p + 1,) if p + 1 < num else None
        start, page = make_page(cnt, start, key, next, af=af)
        yield page


class Thingees(Paged):
    ITEM_KEY = 'thingees'


def thingees(cnt, num, key='thingees', body=Thingees, af=False):
    req = Request('url', 'auth')
    dispatcher = MagicMock(name='dispatcher', )

    # make 5 pages with 5 items on each page
    pages = make_pages(5, 5, key=key, af=af)
    # initial the paged object with the first page
    paged = body(req, mock_http_response(json=next(pages)), dispatcher)
    # the remaining 4 get used here
    dispatcher._dispatch.side_effect = (
        mock_http_response(json=p) for p in pages
    )
    # mimic dispatcher.response
    dispatcher.response = lambda req: Response(req, dispatcher)
    return paged


def test_body_write():
    req = Request('url', 'auth')
    dispatcher = MagicMock(name='dispatcher', )

    chunks = ((str(i) * 16000).encode('utf-8') for i in range(10))
    paged = Paged(req, mock_http_response(
        json=None,
        iter_content=lambda chunk_size: chunks
    ), dispatcher)
    buf = io.BytesIO()
    paged.write(buf)
    assert len(buf.getvalue()) == 160000


def test_paged_items_iter():
    paged = thingees(5, 5)
    expected = 25
    cnt = 0
    for i in paged.items_iter(None):
        if cnt > expected:
            assert False
        assert i['thingee'] == cnt
        cnt += 1
    assert cnt == expected


def test_paged_iter():
    paged = thingees(5, 5)
    pages = list(paged.iter(2))
    assert 2 == len(pages)
    assert 5 == len(pages[0].get()['thingees'])
    assert 5 == len(pages[1].get()['thingees'])


def test_json_encode():
    paged = thingees(5, 5)
    buf = io.StringIO()
    paged.json_encode(buf, 1)
    assert '{"thingees": [{"thingee": 0}]}' == buf.getvalue()


def test_features():
    features = thingees(5, 5, body=Features, key='features')
    buf = io.StringIO()
    features.json_encode(buf, 13)
    features_json = json.loads(buf.getvalue())
    assert features_json['type'] == 'FeatureCollection'
    assert len(features_json['features']) == 13


@pytest.mark.parametrize('limit', [None, 13])
def test_wf3_features(limit):
    pages = 5
    page_size = 6
    num_items = pages * page_size
    features = thingees(page_size, pages,
                        body=WFS3Features,
                        key='features',
                        af=True)
    buf = io.StringIO()
    features.json_encode(buf, limit)
    features_json = json.loads(buf.getvalue())
    assert len(features_json['features']) == limit if limit else num_items
