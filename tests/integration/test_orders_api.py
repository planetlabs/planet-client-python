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

from planet.api.orders_client import OrdersClient

LOGGER = logging.getLogger(__name__)

TEST_API_KEY = '1234'

# fake but real-looking oid
TEST_OID = 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'

STATE_QUEUED = 'queued'


@pytest.fixture()
def ordersapi(tmpdir):
    '''Mocks up the orders api

    Responds to create, poll, and download'''
    _URI_TO_RESPONSE = {
        '/{}'.format(TEST_OID): {
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


def test_get_order(ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    state = cl.get_order(TEST_OID).state
    assert state == STATE_QUEUED


@pytest.mark.skip(reason='not implemented')
def test_download(tmpdir, ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    cl.download(TEST_OID, str(tmpdir))

    # TODO: if state is not 'complete' what do we want to do? do we poll
    # or raise an exception?

    # TODO: check that all files are downloaded


@pytest.mark.skip(reason='not implemented')
def test_create(monkeypatch, ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    # TODO: read in an order creation json blob
    order_desc = None
    oid = cl.create(order_desc)

    # TODO: assert order created successfully and we got oid
    assert oid


@pytest.mark.skip(reason='not implemented')
def test_poll(ordersapi):
    cl = OrdersClient(api_key=TEST_API_KEY, base_url=ordersapi)

    cl.poll(TEST_OID)

    # TODO: assert that this exits out if state isn't queued or running or
    # some finished state, check that it waits until the state is no longer
    # running and that it gracefully handles other states
    # maybe break all those into separate tests
    # need ordersapi to be able to return different responses so state changes
