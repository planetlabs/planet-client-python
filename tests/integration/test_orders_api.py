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
import json
import logging
import math
import os
from pathlib import Path


import httpx
import pytest
import respx

from planet import OrdersClient, Session


TEST_URL = 'http://MockNotRealURL/'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
@pytest.mark.asyncio
async def session():
    async with Session() as ps:
        yield ps


@pytest.fixture
def order_descriptions(order_description):
    order1 = order_description
    order1['id'] = 'oid1'
    order2 = copy.deepcopy(order_description)
    order2['id'] = 'oid2'
    order3 = copy.deepcopy(order_description)
    order3['id'] = 'oid3'
    return [order1, order2, order3]


@respx.mock
@pytest.mark.asyncio
async def test_list_orders_basic(order_descriptions, session):
    list_url = TEST_URL + 'orders/v2/'
    next_page_url = list_url + 'blob/?page_marker=IAmATest'

    order1, order2, order3 = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string",
            "next": next_page_url},
        "orders": [order1, order2]
    }
    mock_resp1 = httpx.Response(200, json=page1_response)
    respx.get(list_url).return_value = mock_resp1

    page2_response = {
        "_links": {
            "_self": next_page_url},
        "orders": [order3]
    }
    mock_resp2 = httpx.Response(200, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = OrdersClient(session, base_url=TEST_URL)
    orders = await cl.list_orders()

    oids = list(o.id for o in orders)
    assert oids == ['oid1', 'oid2', 'oid3']


@respx.mock
@pytest.mark.asyncio
async def test_list_orders_state(order_descriptions, session):
    list_url = TEST_URL + 'orders/v2/?state=failed'

    order1, order2, _ = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string"
        },
        "orders": [order1, order2]
    }
    mock_resp = httpx.Response(200, json=page1_response)
    respx.get(list_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    orders = await cl.list_orders(state='failed')

    oids = list(o.id for o in orders)
    assert oids == ['oid1', 'oid2']


@respx.mock
@pytest.mark.asyncio
async def test_list_orders_limit(order_descriptions, session):
    # check that the client doesn't try to get the next page when the
    # limit is already reached by providing link to next page but not
    # registering a response. if the client tries to get the next
    # page, an error will occur

    list_url = TEST_URL + 'orders/v2/'
    nono_page_url = list_url + '?page_marker=OhNoNo'

    order1, order2, order3 = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string",
            "next": nono_page_url},
        "orders": [order1, order2]
    }
    mock_resp = httpx.Response(200, json=page1_response)

    page2_response = {
        "_links": {
            "_self": "string",
        },
        "orders": [order3]
    }
    mock_resp2 = httpx.Response(200, json=page2_response)

    respx.route(method="GET", url__eq=list_url).mock(return_value=mock_resp)
    nono_route = respx.route(method="GET", url__eq=nono_page_url).mock(
        return_value=mock_resp2)

    cl = OrdersClient(session, base_url=TEST_URL)
    orders = await cl.list_orders(limit=1)

    assert not nono_route.called
    oids = [o.id for o in orders]
    assert oids == ['oid1']


@respx.mock
@pytest.mark.asyncio
async def test_create_order(oid, order_description, order_details, session):
    create_url = TEST_URL + 'orders/v2/'
    mock_resp = httpx.Response(200, json=order_description)
    respx.post(create_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    created_oid = await cl.create_order(order_details)

    assert created_oid == oid


@respx.mock
@pytest.mark.asyncio
async def test_get_order(oid, order_description, session):
    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(200, json=order_description)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    order = await cl.get_order(oid)

    assert order.state == 'queued'


@respx.mock
@pytest.mark.asyncio
async def test_cancel_order(oid, order_description, session):
    cancel_url = TEST_URL + 'orders/v2/' + oid
    order_description['state'] = 'cancelled'
    mock_resp = httpx.Response(200, json=order_description)
    respx.put(cancel_url).return_value = mock_resp

    # TODO: the api says cancel order returns the order details but as
    # far as I can test thus far, it returns nothing. follow up on this
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.cancel_order(oid)


@respx.mock
@pytest.mark.asyncio
async def test_cancel_orders_by_ids(session):
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
    mock_resp = httpx.Response(200, json=example_result)
    respx.post(bulk_cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.cancel_orders(test_ids)

    assert res == example_result

    expected_body = {
            "order_ids": test_ids
    }
    actual_body = json.loads(respx.calls.last.request.content)
    assert actual_body == expected_body


@respx.mock
@pytest.mark.asyncio
async def test_cancel_orders_all(session):
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
    mock_resp = httpx.Response(200, json=example_result)
    respx.post(bulk_cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.cancel_orders()

    assert res == example_result

    actual_body = json.loads(respx.calls.last.request.content)
    assert actual_body == {}


@respx.mock
@pytest.mark.asyncio
async def test_poll(oid, order_description, session):
    get_url = TEST_URL + 'orders/v2/' + oid

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'running'
    order_description3 = copy.deepcopy(order_description)
    order_description3['state'] = 'success'

    cl = OrdersClient(session, base_url=TEST_URL)

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(200, json=order_description),
        httpx.Response(200, json=order_description2),
        httpx.Response(200, json=order_description3)
    ]
    state = await cl.poll(oid, wait=0)
    assert state == 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(200, json=order_description),
        httpx.Response(200, json=order_description2),
        httpx.Response(200, json=order_description3)
    ]
    state = await cl.poll(oid, state='running', wait=0)
    assert state == 'running'


@respx.mock
@pytest.mark.asyncio
async def test_aggegated_order_stats(session):
    stats_url = TEST_URL + 'stats/orders/v2/'
    LOGGER.debug(f'url: {stats_url}')
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
    mock_resp = httpx.Response(200, json=example_stats)
    respx.get(stats_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.aggregated_order_stats()

    assert res == example_stats


@respx.mock
@pytest.mark.asyncio
async def test_download_asset_md(tmpdir, session):
    dl_url = TEST_URL + 'download/?token=IAmAToken'

    md_json = {'key': 'value'}
    md_headers = {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="metadata.json"'
    }
    mock_resp = httpx.Response(200, json=md_json, headers=md_headers)
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    filename = await cl.download_asset(dl_url, directory=str(tmpdir))

    assert json.loads(open(filename).read()) == {'key': 'value'}
    assert Path(filename).name == 'metadata.json'


@respx.mock
@pytest.mark.asyncio
async def test_download_asset_img(tmpdir, open_test_img, session):
    dl_url = TEST_URL + 'download/?token=IAmAToken'

    img_headers = {
        'Content-Type': 'image/tiff',
        'Content-Length': '527',
        'Content-Disposition': 'attachment; filename="img.tif"'
    }

    async def _stream_img():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v)/(chunksize))):
            yield v[i*chunksize:min((i+1)*chunksize, len(v))]

    # populate request parameter to avoid respx cloning, which throws
    # an error caused by respx and not this code
    # https://github.com/lundberg/respx/issues/130
    mock_resp = httpx.Response(200, stream=_stream_img(), headers=img_headers,
                               request='donotcloneme')
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    filename = await cl.download_asset(dl_url, directory=str(tmpdir))

    assert Path(filename).name == 'img.tif'
    assert os.path.isfile(filename)


@respx.mock
@pytest.mark.asyncio
async def test_download_order(tmpdir, order_description, oid, session):
    dl_url1 = TEST_URL + 'download/1?token=IAmAToken'
    dl_url2 = TEST_URL + 'download/2?token=IAmAnotherToken'
    order_description['_links']['results'] = [
        {'location': dl_url1},
        {'location': dl_url2}
    ]

    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(200, json=order_description)
    respx.get(get_url).return_value = mock_resp

    mock_resp1 = httpx.Response(
        200,
        json={'key': 'value'},
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="m1.json"'
        })
    respx.get(dl_url1).return_value = mock_resp1

    mock_resp1 = httpx.Response(
        200,
        json={'key2': 'value2'},
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="m2.json"'
        })
    respx.get(dl_url2).return_value = mock_resp1

    cl = OrdersClient(session, base_url=TEST_URL)
    filenames = await cl.download_order(oid, directory=str(tmpdir))

    assert len(filenames) == 2

    assert json.loads(open(filenames[0]).read()) == {'key': 'value'}
    assert Path(filenames[0]).name == 'm1.json'

    assert json.loads(open(filenames[1]).read()) == {'key2': 'value2'}
    assert Path(filenames[1]).name == 'm2.json'