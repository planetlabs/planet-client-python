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


@pytest.fixture
def mocked_order_http_response():
    test_order = {
        "_links": {
            "_self": "selflocation",
            "results": [
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.262Z",
                    "location": "location1",
                    "name": "name1"
                },
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.264Z",
                    "location": "location2",
                    "name": "name2"
                },
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.267Z",
                    "location": "location3",
                    "name": "name3"
                }
            ]
        },
        "created_on": "2020-12-03T22:20:04.153Z",
        "error_hints": [],
        "id": "adca02a4-58eb-44b3-956f-b09aef7be02a",
        "last_message": "Manifest delivery completed",
        "last_modified": "2020-12-03T22:22:35.619Z",
        "name": "test_order",
        "products": [
            {
                "item_ids": [
                    "3949357_1454705_2020-12-01_241c"
                ],
                "item_type": "PSOrthoTile",
                "product_bundle": "analytic"
            }
        ],
        "state": "success"
    }
    return mock_http_response(json=test_order)


def test_Order_results(mocked_request, mocked_order_http_response):
    order = models.Order(mocked_request, mocked_order_http_response)
    assert len(order.results) == 3


def test_Order_items(mocked_request, mocked_order_http_response):
    order = models.Order(mocked_request, mocked_order_http_response)
    expected_items = ['location1', 'location2', 'location3']
    assert order.items == expected_items


def test_Order_items_iter(mocked_request, mocked_order_http_response):
    order = models.Order(mocked_request, mocked_order_http_response)
    assert next(order.items_iter) == 'location1'


@pytest.fixture
def test_order_details_dict():
    test_order_details = {
      "name": "string",
      "subscription_id": 0,
      "products": [
        {
          "item_ids": [
            "string"
          ],
          "item_type": "psorthotile",
          "product_bundle": "analytic"
        }
      ],
      "delivery": {
        "single_archive": True,
        "archive_type": "string",
        "archive_filename": "string",
        "layout": {
          "format": "standard"
        },
        "amazon_s3": {
          "bucket": "string",
          "aws_region": "string",
          "aws_access_key_id": "string",
          "aws_secret_access_key": "string",
          "path_prefix": "string"
        },
        "azure_blob_storage": {
          "account": "string",
          "container": "string",
          "sas_token": "string",
          "storage_endpoint_suffix": "string",
          "path_prefix": "string"
        },
        "google_cloud_storage": {
          "bucket": "string",
          "credentials": "string",
          "path_prefix": "string"
        },
        "google_earth_engine": {
          "project": "string",
          "collection": "string"
        }
      },
      "notifications": {
        "webhook": {
          "url": "string",
          "per_order": True
        },
        "email": True
      },
      "order_type": "full",
      "tools": [
        {
          "anchor_item": "string",
          "method": "string",
          "anchor_bundle": "string",
          "strict": True
        }
      ]
    }
    return test_order_details


def test_OrderDetails_substitute_supported():
    key = 'abc'
    supported = ['Supported', 'whyamihere']

    # ensure capitalization doesn't matter
    valid_product = {key: 'supported'}
    models.OrderDetails._substitute_supported(valid_product, key, supported)
    assert valid_product[key] == 'Supported'

    # ensure an exception is raised when the entry is not supported
    invalid_product = {key: 'notsupported'}
    with pytest.raises(models.OrderDetailsException):
        models.OrderDetails._substitute_supported(
            invalid_product, key, supported)


def test_OrderDetails__validate_details_valid(test_order_details_dict):
    test_order_details_dict['products'][0]['product_bundle'] = 'ANALYTIC'
    test_order_details_dict['products'][0]['item_type'] = 'psorthotile'

    _ = models.OrderDetails(test_order_details_dict)


def test_OrderDetails__validate_details_invalid(test_order_details_dict):
    invalid_bundle = test_order_details_dict.copy()
    invalid_bundle['products'][0]['product_bundle'] = 'nope'

    with pytest.raises(models.OrderDetailsException):
        _ = models.OrderDetails(invalid_bundle)

    invalid_item = test_order_details_dict.copy()
    invalid_item['products'][0]['product_bundle'] = 'ANALYTIC'
    invalid_item['products'][0]['item_type'] = 'nope'

    with pytest.raises(models.OrderDetailsException):
        _ = models.OrderDetails(invalid_item)


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
