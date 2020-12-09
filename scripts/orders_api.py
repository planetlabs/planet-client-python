# Copyright 2020 Planet Labs, Inc.
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

'''
Test interactions with the API to get real responses for test mocking
'''
import json
import logging
import os
import sys
import time

from planet.api import http, models, OrdersClient

ORDERS_URL = 'https://api.planet.com/compute/ops/orders/v2/'

API_KEY = os.getenv('PL_API_KEY')

LOGGER = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Request(object):
    def __init__(self, url, body_type, method, headers, data=None):
        self.url = url
        self.body_type = body_type
        self.method = method
        self.headers = headers

        self.params = None
        self.data = data


def trigger_throttle():
    url = ORDERS_URL
    body_type = models.Order
    method = 'GET'
    headers = {'Authorization': 'api-key %s' % API_KEY}
    req = Request(url, body_type, method, headers)

    with http.PlanetSession() as sess:
        t = time.time()
        for i in range(15):
            resp = sess.request(req)
            print(time.time() - t)
            print(resp)


def trigger_unauth():
    url = ORDERS_URL
    body_type = models.Order
    method = 'GET'
    headers = {'Authorization': 'api-key %s' % 'nope'}
    req = Request(url, body_type, method, headers)

    with http.PlanetSession() as sess:
        resp = sess.request(req)
        print(resp)


TEST_ORDER = {
      "name": "test_order",
      "products": [
        {
          "item_ids": [
            "3949357_1454705_2020-12-01_241c"
          ],
          "item_type": "PSOrthoTile",
          "product_bundle": "analytic"
        }
      ]
    }


def create_order():
    url = ORDERS_URL
    body_type = models.Order
    method = 'POST'
    headers = {
        'Authorization': 'api-key %s' % API_KEY,
        'Content-Type': 'application/json'
    }

    data = json.dumps(TEST_ORDER)
    req = Request(url, body_type, method, headers, data=data)

    with http.PlanetSession() as sess:
        resp = sess.request(req)
        print(resp)
        print(resp.body.get_raw())


def create_order_client():
    cl = OrdersClient()
    oid = cl.create_order(TEST_ORDER)
    print(oid)
    return oid


def cancel_order_client(oid):
    cl = OrdersClient()
    cancelled = cl.cancel_order(oid)
    print(cancelled.response.headers)
    print(cancelled.response.content)
    # print(cancelled)
    # print(cancelled)


def run():
    # trigger_unauth()
    # trigger_throttle()
    # create_order()
    oid = create_order_client()
    print(oid)
    cancel_order_client(oid)


if __name__ == '__main__':
    run()
