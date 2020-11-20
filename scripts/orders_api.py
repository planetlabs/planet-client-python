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
import os
import time

from planet.api import http, models

ORDERS_URL = 'https://api.planet.com/compute/ops/orders/v2/'

API_KEY = os.getenv('PL_API_KEY')


class Request(object):
    def __init__(self, url, body_type, method, headers):
        self.url = url
        self.body_type = body_type
        self.method = method
        self.headers = headers

        self.params = None
        self.data = None


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


def run():
    # trigger_unauth()
    # trigger_throttle()


if __name__ == '__main__':
    run()
