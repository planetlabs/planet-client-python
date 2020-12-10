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
import copy
import logging

import pytest
import requests_mock

from planet.api import OrdersClient

LOGGER = logging.getLogger(__name__)

TEST_API_KEY = '1234'

# if use mock:// as the prefix, the params get lost
# https://github.com/jamielennox/requests-mock/issues/142
TEST_URL = 'http://MockNotRealURL/'

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


@pytest.fixture()
def orders_client():
    return OrdersClient(api_key=TEST_API_KEY, base_url=TEST_URL)


def test_get_order(orders_client):
    with requests_mock.Mocker() as m:
        get_url = TEST_URL + 'orders/v2/' + TEST_OID
        m.get(get_url, status_code=200, json=ORDER_DESCRIPTION)

        state = orders_client.get_order(TEST_OID).state
        assert state == STATE_QUEUED


def test_list_orders(orders_client):
    with requests_mock.Mocker() as m:
        list_url = TEST_URL + 'orders/v2/'
        next_page_url = list_url + '?page_marker=IAmATest'

        order1 = copy.deepcopy(ORDER_DESCRIPTION)
        order1['id'] = 'oid1'
        order2 = copy.deepcopy(ORDER_DESCRIPTION)
        order2['id'] = 'oid2'
        order3 = copy.deepcopy(ORDER_DESCRIPTION)
        order3['id'] = 'oid3'

        page1_response = {
            "_links": {
                "_self": "string",
                "next": next_page_url},
            "orders": [order1, order2]
        }
        m.get(list_url, status_code=200, json=page1_response)

        page2_response = {
            "_links": {
                "_self": next_page_url},
            "orders": [order3]
        }
        m.get(next_page_url, status_code=200, json=page2_response)

        orders = orders_client.list_orders()
        oids = list(o.id for o in orders)
        assert oids == ['oid1', 'oid2', 'oid3']


def test_list_orders_state(orders_client):
    with requests_mock.Mocker() as m:
        list_url = TEST_URL + 'orders/v2/?state=failed'

        order1 = copy.deepcopy(ORDER_DESCRIPTION)
        order1['id'] = 'oid1'
        order2 = copy.deepcopy(ORDER_DESCRIPTION)
        order2['id'] = 'oid2'

        page1_response = {
            "_links": {
                "_self": "string"
            },
            "orders": [order1, order2]
        }
        m.get(list_url, status_code=200, json=page1_response)

        orders = orders_client.list_orders(state='failed')
        oids = list(o.id for o in orders)
        assert oids == ['oid1', 'oid2']


def test_list_orders_limit(orders_client):
    with requests_mock.Mocker() as m:
        list_url = TEST_URL + 'orders/v2/'
        next_page_url = list_url + '?page_marker=IAmATest'

        order1 = copy.deepcopy(ORDER_DESCRIPTION)
        order1['id'] = 'oid1'
        order2 = copy.deepcopy(ORDER_DESCRIPTION)
        order2['id'] = 'oid2'
        order3 = copy.deepcopy(ORDER_DESCRIPTION)
        order3['id'] = 'oid3'

        # check that the client doesn't try to get the next page when the
        # limit is already reached by providing link to next page but not
        # registering a response. if the client tries to get the next
        # page, an error will occur
        page1_response = {
            "_links": {
                "_self": "string",
                "next": next_page_url},
            "orders": [order1, order2]
        }
        m.get(list_url, status_code=200, json=page1_response)

        orders = orders_client.list_orders(limit=1)
        oids = list(o.id for o in orders)
        assert oids == ['oid1']


def test_create_order(orders_client):
    with requests_mock.Mocker() as m:
        create_url = TEST_URL + 'orders/v2/'
        m.post(create_url, status_code=200, json=ORDER_DESCRIPTION)

        oid = orders_client.create_order(ORDER_DETAILS)
        assert oid == TEST_OID


def test_cancel_order(orders_client):
    # TODO: the api says cancel order returns the order details but as
    # far as I can test thus far, it returns nothing. follow up on this
    with requests_mock.Mocker() as m:
        cancel_url = TEST_URL + 'orders/v2/' + TEST_OID
        m.put(cancel_url, status_code=200, text='')

        orders_client.cancel_order(TEST_OID)


def test_cancel_orders(orders_client):
    with requests_mock.Mocker() as m:
        bulk_cancel_url = TEST_URL + 'bulk/orders/v2/cancel'

        test_ids = ["oid1", "oid2", "oid3"]
        example_result = {
            "result": {
                "succeeded": {"count": 2},
                "failed": {
                    "count": 1,
                    "failures": [
                        {
                            "order_id": "oid3",
                            "message": "bummer"
                        }
                    ]
                }
            }
        }
        m.post(bulk_cancel_url, status_code=200, json=example_result)

        res = orders_client.cancel_orders(test_ids)
        assert res == example_result

        expected_body = {
                "order_ids": test_ids
        }
        history = m.request_history
        assert history[0].json() == expected_body


def test_cancel_orders_all(orders_client):
    with requests_mock.Mocker() as m:
        bulk_cancel_url = TEST_URL + 'bulk/orders/v2/cancel'

        example_result = {
            "result": {
                "succeeded": {"count": 2},
                "failed": {
                    "count": 0,
                    "failures": []
                }
            }
        }
        m.post(bulk_cancel_url, status_code=200, json=example_result)

        res = orders_client.cancel_orders([])
        assert res == example_result

        history = m.request_history
        assert history[0].json() == {}


def test_aggegated_order_stats(orders_client):
    with requests_mock.Mocker() as m:
        stats_url = TEST_URL + 'stats/orders/v2/'
        LOGGER.debug('url: {}'.format(stats_url))
        example_stats = {
            "organization": {
                "queued_orders": 0,
                "running_orders": 6
            },
            "user": {
                "queued_orders": 0,
                "running_orders": 0
            }
        }
        m.get(stats_url, status_code=200, json=example_stats)

        res = orders_client.aggregated_order_stats()
        assert res == example_stats


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
