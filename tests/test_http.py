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

from http.server import BaseHTTPRequestHandler
import json
import logging
from multiprocessing import Process
import os
import random
import signal
import socketserver

import pytest

from planet.api import auth, exceptions, http, models

LOGGER = logging.getLogger(__name__)

TEST_API_KEY = '1234'

# fake but real-looking oid
TEST_OID = 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'


@pytest.fixture()
def ordersapi(tmpdir):
    '''Mocks up the orders api

    Responds to create, poll, and download'''
    _URI_TO_RESPONSE = {
        '/compute/ops/orders/v2/{}'.format(TEST_OID): {
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
            "state": "queued",
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
        },

    }

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path not in _URI_TO_RESPONSE:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.end_headers()
            resp = json.dumps(_URI_TO_RESPONSE[self.path]).encode('utf-8')
            self.wfile.write(resp)

    socketserver.TCPServer.allow_reuse_address = True
    port = random.randint(10000, 20000)
    handler = SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    path = os.path.join(str(tmpdir))

    p = Process(target=_cwd_and_serve, args=(httpd, path))
    p.daemon = True
    p.start()
    yield 'http://localhost:{}'.format(port)

    os.kill(p.pid, signal.SIGTERM)


def _cwd_and_serve(httpd, path):
    os.chdir(path)
    httpd.serve_forever()


def test_planetsession_contextmanager():
    with http.PlanetSession():
        pass


def test_planetsession_request_responsebody(ordersapi):
    ps = http.PlanetSession()

    url = ordersapi + '/compute/ops/orders/v2/{}'.format(TEST_OID)

    key = auth.APIKey(TEST_API_KEY)
    body_type = models.Order
    method = 'GET'
    req = models.Request(url, key, body_type=body_type, method=method)
    resp = ps.request(req)
    assert isinstance(resp.body, body_type)


def test_planetsession_request_missingresource(ordersapi):
    ps = http.PlanetSession()

    NOT_TEST_ID = '5'
    url = ordersapi + '/compute/ops/orders/v2/{}'.format(NOT_TEST_ID)

    key = auth.APIKey(TEST_API_KEY)
    body_type = models.Order
    method = 'GET'
    req = models.Request(url, key, body_type=body_type, method=method)
    with pytest.raises(exceptions.MissingResource):
        ps.request(req)


# @pytest.fixture()
# def throttleapi(tmpdir):
#     '''Mocks up the api throttling the user'''
#     _URI_TO_RESPONSE = {
#         '/': {}
#     }
#
#     class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
#         def __init__(self, *args, **kwargs):
#             LOGGER.warning('its a new me')
#             self.throttled = False
#             super(SimpleHTTPRequestHandler, self).__init__(*args, **kwargs)
#
#         def do_GET(self):
#             if self.path not in _URI_TO_RESPONSE:
#                 self.send_response(404)
#                 self.end_headers()
#                 return
#
#             # throw in a throttle to check retry
#             LOGGER.info('before: {}'.format(self.throttled))
#             if not self.throttled:
#                 self.throttled = True
#                 LOGGER.info('HERE HERE')
#                 LOGGER.info(self.throttled)
#                 self.send_response(429)
#                 self.end_headers()
#
#             self.send_response(200)
#             self.end_headers()
#             resp = json.dumps(_URI_TO_RESPONSE[self.path]).encode('utf-8')
#             self.wfile.write(resp)
#
#     socketserver.TCPServer.allow_reuse_address = True
#     port = random.randint(10000, 20000)
#     handler = SimpleHTTPRequestHandler
#     httpd = socketserver.TCPServer(("", port), handler)
#     path = os.path.join(str(tmpdir))
#
#     p = Process(target=_cwd_and_serve, args=(httpd, path))
#     p.daemon = True
#     p.start()
#     yield 'http://localhost:{}'.format(port)
#
#     os.kill(p.pid, signal.SIGTERM)


# def test_planetsession_retry(throttleapi):
#     ps = http.PlanetSession()
#
#     url = throttleapi
#
#     key = auth.APIKey(TEST_API_KEY)
#     body_type = models.Order
#     method = 'GET'
#     req = models.Request(url, key, body_type=body_type, method=method)
#     ps.request(req)
