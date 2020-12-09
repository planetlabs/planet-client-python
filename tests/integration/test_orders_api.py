# Copyright 2020 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import logging

import pytest
import requests_mock

from planet.api import OrdersClient

LOGGER = logging.getLogger(__name__)

TEST_API_KEY = '1234'
TEST_URL = 'mock://test.com'
# fake but real-looking oid
TEST_OID = 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'

STATE_QUEUED = 'queued'

ORDER_DESCRIPTION = {
    "_links": {
        "_self": "string",
        "results": [
            {
                "location": "/foo"
            }
        ]
    },
    "id": TEST_OID,
    "name": "string",
    "subscription_id": 0,
    "tools": [{}],
    "products": [{}],
    "created_on": "2019-08-24T14:15:22Z",
    "last_modified": "2019-08-24T14:15:22Z",
    "state": STATE_QUEUED,
    "last_message": "string",
    "error_hints": [
        "string"
    ],
    "delivery": {
        "single_archive": True,
        "archive_type": "string",
        "archive_filename": "string",
        "layout": {},
        "amazon_s3": {},
        "azure_blob_storage": {},
        "google_cloud_storage": {},
        "google_earth_engine": {}
    },
    "notifications": {
        "webhook": {},
        "email": True
    },
    "order_type": "full"
}

ORDER_DETAILS = {
      "name": "test_order",
      "products": [
        {
          "item_ids": [
            "test_item_id"
          ],
          "item_type": 'PSOrthoTile',
          "product_bundle": 'ANALYTIC'
        }
      ],
      "delivery": {
        "single_archive": True,
        "archive_type": "string",
        "archive_filename": "string",
        "layout": {
          "format": "standard"
        }},
      "tools": [
        {
          "anchor_item": "string",
          "method": "string",
          "anchor_bundle": "string",
          "strict": True
        }
      ]
}


def test_get_order():
    with requests_mock.Mocker() as m:
        get_url = TEST_URL + '/' + TEST_OID
        m.get(get_url, status_code=200, json=ORDER_DESCRIPTION)

        cl = OrdersClient(api_key=TEST_API_KEY, base_url=TEST_URL)

        state = cl.get_order(TEST_OID).state
        assert state == STATE_QUEUED


def test_create_order():
    with requests_mock.Mocker() as m:
        create_url = TEST_URL
        m.post(create_url, status_code=200, json=ORDER_DESCRIPTION)

        cl = OrdersClient(api_key=TEST_API_KEY, base_url=TEST_URL)
        oid = cl.create_order(ORDER_DETAILS)
        assert oid == TEST_OID


def test_cancel_order():
    # TODO: the api says cancel order returns the order details but as
    # far as I can test thus far, it returns nothing. follow up on this
    with requests_mock.Mocker() as m:
        cancel_url = TEST_URL + '/' + TEST_OID
        m.put(cancel_url, status_code=200, text='success')

        cl = OrdersClient(api_key=TEST_API_KEY, base_url=TEST_URL)
        res = cl.cancel_order(TEST_OID)
        assert res.get_raw() == 'success'


@pytest.mark.skip(reason='not implemented')
def test_download(tmpdir, ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    cl.download(TEST_OID, str(tmpdir))

    # TODO: if state is not 'complete' what do we want to do? do we poll
    # or raise an exception?

    # TODO: check that all files are downloaded


@pytest.mark.skip(reason='not implemented')
def test_poll(ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    cl.poll(TEST_OID)

    # TODO: assert that this exits out if state isn't queued or running or
    # some finished state, check that it waits until the state is no longer
    # running and that it gracefully handles other states
    # maybe break all those into separate tests
    # need ordersapi to be able to return different responses so state changes
