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

import pytest

from planet import OrderClient

@pytest.fixture()
def ordersapi(tmpdir):
    '''Mocks up the orders api

    Responds to create, poll, and download'''
    raise NotImplementedError


def test_create(monkeypatch, ordersapi):
    monkeypatch.setenv('PL_API_BASE_URL', ordersapi)
    monkeypatch.setenv('PL_API_KEY', '1234')

    # TODO: get auth
    auth = None
    cl = OrderClient(auth)

    # TODO: read in an order creation json blob
    order_desc = None
    oid = cl.create(order_desc)

    # TODO: assert order created successfully and we got oid


def test_check_state(ordersapi):
    # TODO: get auth
    auth = None
    cl = OrderClient(auth)

    # TODO: figure out real looking oid
    oid = 'mock but real looking oid'
    cl.check_state(oid)

    # TODO: assert status check successful and accurate


def test_poll(ordersapi):
    # TODO: get auth
    auth = None
    cl = OrderClient(auth)

    # TODO: figure out real looking oid
    oid = 'mock but real looking oid'
    cl.poll(oid)

    # TODO: assert that this exits out if state isn't queued or running or
    # some finished state, check that it waits until the state is no longer
    # running and that it gracefully handles other states
    # maybe break all those into separate tests
    # need ordersapi to be able to return different responses so state changes


def test_download(ordersapi):
    # TODO: get auth
    auth = None
    cl = OrderClient(auth)

    # TODO: figure out real looking oid
    oid = 'mock but real looking oid'
    cl.download(oid)

    # TODO: if state is not 'complete' what do we want to do? do we poll
    # or raise an exception?

    # TODO: check that all files are downloaded
