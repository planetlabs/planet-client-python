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
    print(cancelled)
    # print(cancelled.response.headers)
    # print(cancelled.response.content)


def cancel_orders_client(oid):
    cl = OrdersClient()
    cancelled = cl.cancel_orders([oid])
    print(cancelled)


def cancel_orders_client_all():
    cl = OrdersClient()
    cancelled = cl.cancel_orders([])
    print(cancelled)


def list_orders():
    # for i in range(50):
    #     create_order_client()

    cl = OrdersClient()
    # orders = cl.list_orders()
    orders = cl.list_orders(state='success')
    # orders = cl.list_orders(state='failed')
    for o in orders:
        print(o.state)


def download_asset():
    cl = OrdersClient()
    # # metadata
    # location = "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDc3MjU4MDgsInN1YiI6Ikd0TC9Nb1EvSU1UTzRFTWxrU3Fxc09TaUtpUDZVbldSc1lzdlRlYlY4elNzOXUzSzRlSk9aQ0J4N2ZvY3JKOGxyY1FzVHI2aHVlK2NnbEpZNGdOa1p3PT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS9mOGRhMGEzZS0xNzRmLTQzNTktYjA4OC1hOTYxYWM3NmYwZTcvUFNPcnRob1RpbGUvMzk0OTM1N18xNDU0NzA1XzIwMjAtMTItMDFfMjQxY19tZXRhZGF0YS5qc29uP0V4cGlyZXM9MTYwNzcyNTgwOFx1MDAyNkdvb2dsZUFjY2Vzc0lkPWNvbXB1dGUtZ2NzLXN2Y2FjYyU0MHBsYW5ldC1jb21wdXRlLXByb2QuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb21cdTAwMjZTaWduYXR1cmU9QnRqQUtqUXY2R1hUWnNjYm5MUU45UWw4JTJCcG5neFBDek1hVkhVeTRkUmR6NU5JNW5YSUZ1NkxWOTZrSzkyVTBzMjF6WkJ1bmVpZ0VVdVRBd3FpaFdsSmdsc29DTGJGMXl3NnIzSllNdDNSSlRvaU11Qm0yVkRZQnVzWVlCZWlSUnMxaVQyeFprTnhmenZPcTQ2QWQyQTB1dzNBeEpzalVJZnNhMW5SeWtEVHE0dVFTOUVpRnhFYjJOYWJFOGk2Z3lySWM5dUVwQkRxSXZVOSUyQk9mRTdXc3hDQ2hFNmlJclJoZ1ZkaUk5SVJlSDNTSk1oQ3Zja2Z1aXVySjRqRWl3VU5MeFNKRExxMmVYMkF3cldFT3hGeDhxSDcxZ0dnMjk0MmtYSkNzeXVaTEw5YUtWNGM1ckEzNkJDMG1QT2dncW9vUzQ1ZzUwODBCa2JOOCUyQmw5eUJsTmxBJTNEJTNEIiwic291cmNlIjoiT3JkZXJzIFNlcnZpY2UifQ.zjcMsv4vntuzSnBCSjPotlGHkV0F6QaL9WgGYYHYosCh6xKEoEgdA90rWPSm90nc5kdP3ch8o9cbory5N4_cdA" # noqa E501

    # img

    location = "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDc5MDMzMzcsInN1YiI6IlJrM1BCNGIrY2VHb1RzQ2VxbGIwKzRFZmRnUWRYaGJiY3p3N1dMR0paczB5cGVOcEVqTVhGdWtqOWg5dVlMdkZMb05ZVGdNdTgrOTJrajdyWHg5VWJnPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS84NWMwODkxOC1mNGJmLTRlMjYtYjE2Yy0xMjhlMzJhNjZjMjYvUFNPcnRob1RpbGUvMzk0OTM1N18xNDU0NzA1XzIwMjAtMTItMDFfMjQxY19CR1JOX0FuYWx5dGljLnRpZj9FeHBpcmVzPTE2MDc5MDMzMzdcdTAwMjZHb29nbGVBY2Nlc3NJZD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tXHUwMDI2U2lnbmF0dXJlPW5BVEVIYzR5OUw2RXQ0Y3glMkJkSXU3dHVvOVRQMFBoQ1R1bXFsYW1ZcmJCRHJnMUYxdVJzSiUyQmpXRTkxcFhwR3JINUxnJTJGaVRGcnglMkJlRjZGU0dKcTFua3Rmd2k5YTFabDZnZFlCUUhxSVVNVWFRbnRpY29ibmlZajVtJTJCZWJhbGpuOXlubjBvTHNjOWRDMHV0b1N3TllIMnZOTU9yNVJUaGF6ZjVhaG9ES1JVOE9mV0QlMkZ4dWZXWXdWSHhUTiUyQlhqVlpmeTVXJTJGTW02TWxpMDglMkZjJTJGRlI1JTJGVnJUUFZRZERZMlU3cktEYUJ2SDhBTWVwcHVWT2ZCNXNYdDBnQXMzVzlIYkhNdVdaJTJGbkxEb0EzVlBqZzUxMFVzTUN6VXNRbGNIWWMlMkZnUDZUTVdZWVB3SHFRNlFSeVA4NlpLOGJ2V1F4JTJCYzJYYW9GWHE1OEllazFHJTJCOHFxc0VONVZ1USUzRCUzRCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.16YtuLb4qzv2Q_DNe1068v-qY9xpB_JpwGks9x8IlAb0Sh1lTA_YpibSXEyG4Obys5p1fgTd3aA9H-tawgrW0Q" # noqa E501

    filename = cl.download_asset(location)
    LOGGER.warning(filename)


def run():
    # trigger_unauth()
    # trigger_throttle()
    # create_order()
    # create_order_client()
    # oid = create_order_client(); cancel_order_client(oid)  # noqa: E702
    # oid = create_order_client(); cancel_orders_client(oid)  # noqa: E702
    # create_order_client(); cancel_orders_client_all()  # noqa: E702
    # list_orders()
    LOGGER.warning('API KEY: {}'.format(API_KEY))
    download_asset()


if __name__ == '__main__':
    run()
