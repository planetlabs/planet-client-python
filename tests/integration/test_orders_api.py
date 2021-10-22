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
from http import HTTPStatus
import logging
import math
import os
from pathlib import Path

import httpx
import pytest
import respx

from planet import OrdersClient, clients, exceptions


TEST_URL = 'http://MockNotRealURL/'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def order_descriptions(order_description):
    order1 = order_description
    order1['id'] = 'oid1'
    order2 = copy.deepcopy(order_description)
    order2['id'] = 'oid2'
    order3 = copy.deepcopy(order_description)
    order3['id'] = 'oid3'
    return [order1, order2, order3]


@pytest.fixture
def oid2():
    # obtained from uuid.uuid1()
    return '5ece1dc0-ea81-11eb-837c-acde48001122'


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
    mock_resp1 = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(list_url).return_value = mock_resp1

    page2_response = {
        "_links": {
            "_self": next_page_url},
        "orders": [order3]
    }
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
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
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(list_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    orders = await cl.list_orders(state='failed')

    oids = list(o.id for o in orders)
    assert oids == ['oid1', 'oid2']


@pytest.mark.asyncio
async def test_list_orders_state_invalid_state(session):
    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.list_orders(state='invalidstate')


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
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)

    page2_response = {
        "_links": {
            "_self": "string",
        },
        "orders": [order3]
    }
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)

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
async def test_list_orders_asjson(order_descriptions, session):
    list_url = TEST_URL + 'orders/v2/'

    order1, order2, order3 = order_descriptions

    page1_response = {
        "_links": {"_self": "string"},
        "orders": [order1]
    }
    mock_resp1 = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(list_url).return_value = mock_resp1

    cl = OrdersClient(session, base_url=TEST_URL)
    orders = await cl.list_orders(as_json=True)
    assert orders[0]['id'] == 'oid1'


@respx.mock
@pytest.mark.asyncio
async def test_create_order(oid, order_description, order_request, session):
    create_url = TEST_URL + 'orders/v2/'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.post(create_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    order = await cl.create_order(order_request)

    assert order.json == order_description


@respx.mock
@pytest.mark.asyncio
async def test_create_order_bad_item_type(order_request, session):
    create_url = TEST_URL + 'orders/v2/'

    resp = {
        "field": {
            "Products": [
                {
                    "message": ("Bad item type 'invalid' for bundle type " +
                                "'analytic'")
                }
            ]
        },
        "general": [
            {
                "message": "Unable to accept order"
            }
        ]
    }
    mock_resp = httpx.Response(400, json=resp)
    respx.post(create_url).return_value = mock_resp
    order_request['products'][0]['item_type'] = 'invalid'
    cl = OrdersClient(session, base_url=TEST_URL)

    expected_msg = (
        "Unable to accept order - Bad item type 'invalid' for bundle type " +
        "'analytic'")

    with pytest.raises(exceptions.BadQuery, match=expected_msg):
        _ = await cl.create_order(order_request)


@respx.mock
@pytest.mark.asyncio
async def test_create_order_item_id_does_not_exist(
        order_request, session, match_pytest_raises):
    create_url = TEST_URL + 'orders/v2/'

    resp = {
        "field": {
            "Details": [
                {
                    "message": ("Item ID 4500474_2133707_2021-05-20_2419 / " +
                                "Item Type PSScene3Band doesn't exist")
                }
            ]
        },
        "general": [
            {
                "message": "Unable to accept order"
            }
        ]
    }
    mock_resp = httpx.Response(400, json=resp)
    respx.post(create_url).return_value = mock_resp
    order_request['products'][0]['item_ids'] = \
        '4500474_2133707_2021-05-20_2419'
    cl = OrdersClient(session, base_url=TEST_URL)

    expected_msg = (
        "Unable to accept order - Item ID 4500474_2133707_2021-05-20_2419 " +
        "/ Item Type PSScene3Band doesn't exist")

    with match_pytest_raises(exceptions.BadQuery, expected_msg):
        _ = await cl.create_order(order_request)


@respx.mock
@pytest.mark.asyncio
async def test_get_order(oid, order_description, session):
    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    order = await cl.get_order(oid)

    assert order.state == 'queued'


@pytest.mark.asyncio
async def test_get_order_invalid_id(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.get_order('-')


@respx.mock
@pytest.mark.asyncio
async def test_get_order_id_doesnt_exist(
        oid, session, match_pytest_raises):
    get_url = TEST_URL + 'orders/v2/' + oid

    msg = f'Could not load order ID: {oid}.'
    resp = {
        "message": msg
    }
    mock_resp = httpx.Response(404, json=resp)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with match_pytest_raises(exceptions.MissingResource, msg):
        _ = await cl.get_order(oid)


@respx.mock
@pytest.mark.asyncio
async def test_cancel_order(oid, order_description, session):
    cancel_url = TEST_URL + 'orders/v2/' + oid
    order_description['state'] = 'cancelled'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.put(cancel_url).return_value = mock_resp

    # TODO: the api says cancel order returns the order details but as
    # far as I can test thus far, it returns nothing. follow up on this
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.cancel_order(oid)


@pytest.mark.asyncio
async def test_cancel_order_invalid_id(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.cancel_order('invalid_order_id')


@respx.mock
@pytest.mark.asyncio
async def test_cancel_order_id_doesnt_exist(
        oid, session, match_pytest_raises):
    cancel_url = TEST_URL + 'orders/v2/' + oid

    msg = f'No such order ID: {oid}.'
    resp = {
        "message": msg
    }
    mock_resp = httpx.Response(404, json=resp)
    respx.put(cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with match_pytest_raises(exceptions.MissingResource, msg):
        _ = await cl.cancel_order(oid)


@respx.mock
@pytest.mark.asyncio
async def test_cancel_order_id_cannot_be_cancelled(
        oid, session, match_pytest_raises):
    cancel_url = TEST_URL + 'orders/v2/' + oid

    msg = 'Order not in a cancellable state'
    resp = {
        "message": msg
    }
    mock_resp = httpx.Response(409, json=resp)
    respx.put(cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with match_pytest_raises(exceptions.Conflict, msg):
        _ = await cl.cancel_order(oid)


@respx.mock
@pytest.mark.asyncio
async def test_cancel_orders_by_ids(session, oid, oid2):
    bulk_cancel_url = TEST_URL + 'bulk/orders/v2/cancel'
    test_ids = [oid, oid2]
    example_result = {
        "result": {
            "succeeded": {"count": 1},
            "failed": {
                "count": 1,
                "failures": [
                    {
                        "order_id": oid2,
                        "message": "Order not in a cancellable state",
                    }
                ]
            }
        }
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_result)
    respx.post(bulk_cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.cancel_orders(test_ids)

    assert res == example_result

    expected_body = {
            "order_ids": test_ids
    }
    actual_body = json.loads(respx.calls.last.request.content)
    assert actual_body == expected_body


@pytest.mark.asyncio
async def test_cancel_orders_by_ids_invalid_id(session, oid):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.cancel_orders([oid, "invalid_oid"])


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
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_result)
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
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2),
        httpx.Response(HTTPStatus.OK, json=order_description3)
    ]
    state = await cl.poll(oid, wait=0)
    assert state == 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2),
        httpx.Response(HTTPStatus.OK, json=order_description3)
    ]
    state = await cl.poll(oid, state='running', wait=0)
    assert state == 'running'


@pytest.mark.asyncio
async def test_poll_invalid_oid(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.poll("invalid_oid", wait=0)


@pytest.mark.asyncio
async def test_poll_invalid_state(oid, session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(clients.orders.OrdersClientException):
        _ = await cl.poll(oid, state="invalid_state", wait=0)


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
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_stats)
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
    mock_resp = httpx.Response(HTTPStatus.OK, json=md_json, headers=md_headers)
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
    mock_resp = httpx.Response(HTTPStatus.OK, stream=_stream_img(),
                               headers=img_headers,
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
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    mock_resp1 = httpx.Response(
        HTTPStatus.OK,
        json={'key': 'value'},
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="m1.json"'
        })
    respx.get(dl_url1).return_value = mock_resp1

    mock_resp2 = httpx.Response(
        HTTPStatus.OK,
        json={'key2': 'value2'},
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="m2.json"'
        })
    respx.get(dl_url2).return_value = mock_resp2

    cl = OrdersClient(session, base_url=TEST_URL)
    filenames = await cl.download_order(oid, directory=str(tmpdir))

    assert len(filenames) == 2

    assert json.loads(open(filenames[0]).read()) == {'key': 'value'}
    assert Path(filenames[0]).name == 'm1.json'

    assert json.loads(open(filenames[1]).read()) == {'key2': 'value2'}
    assert Path(filenames[1]).name == 'm2.json'


@respx.mock
@pytest.mark.asyncio
async def test_download_order_overwrite_true_preexisting_data(
        tmpdir, order_description, oid, session):
    '''
    Test if download_order() overwrites pre-existing data with
    overwrite flag set to True.
    '''

    # Create a JSON
    original_content = {'key': 'original_file'}
    # Save JSON to tmpdir
    f = open(Path(tmpdir, 'file.json'), "a")
    f.write(json.dumps(original_content))
    f.close()

    # Create mock HTTP response
    dl_url = TEST_URL + 'download/1?token=IAmAToken'
    order_description['_links']['results'] = [
        {'location': dl_url},
    ]

    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    downloaded_content = {'key': 'downloaded_file'}
    mock_resp = httpx.Response(
        HTTPStatus.OK,
        json=downloaded_content,
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="file.json"'
        })
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    # Download order and overwrite data
    _ = await cl.download_order(oid, directory=str(tmpdir), overwrite=True)

    assert json.loads(open(Path(tmpdir, 'file.json')).read()) != ...
    downloaded_content


@respx.mock
@pytest.mark.asyncio
async def test_download_order_overwrite_false_preexisting_data(
        tmpdir, order_description, oid, session):
    '''
    Test if download_order() does not overwrite pre-existing
    data with overwrite flag set to False.
    '''

    # Create a JSON
    original_content = {'key': 'original_file'}
    # Save JSON to tmpdir
    f = open(Path(tmpdir, 'file.json'), "a")
    f.write(json.dumps(original_content))
    f.close()

    # Create mock HTTP response
    dl_url = TEST_URL + 'download/1?token=IAmAToken'
    order_description['_links']['results'] = [
        {'location': dl_url},
    ]

    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    downloaded_content = {'key': 'downloaded_file'}
    mock_resp = httpx.Response(
        HTTPStatus.OK,
        json=downloaded_content,
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="file.json"'
        })
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    # Download order and overwrite data
    _ = await cl.download_order(oid, directory=str(tmpdir), overwrite=False)

    assert json.loads(open(Path(tmpdir, 'file.json')).read()) != ...
    original_content


@respx.mock
@pytest.mark.asyncio
async def test_download_order_overwrite_true_nonexisting_data(
        tmpdir, order_description, oid, session):
    '''
    Test if download_order() downloads data with overwrite flag
    set to true without pre-existing data.
    '''

    # Create mock HTTP response
    dl_url = TEST_URL + 'download/1?token=IAmAToken'
    order_description['_links']['results'] = [
        {'location': dl_url},
    ]

    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    downloaded_content = {'key': 'downloaded_file'}
    mock_resp = httpx.Response(
        HTTPStatus.OK,
        json=downloaded_content,
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="file.json"'
        })
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    # Download order and overwrite data
    _ = await cl.download_order(oid, directory=str(tmpdir), overwrite=True)

    assert json.loads(open(Path(tmpdir, 'file.json')).read()) != ...
    downloaded_content


@respx.mock
@pytest.mark.asyncio
async def test_download_order_overwrite_false_nonexisting_data(
        tmpdir, order_description, oid, session):
    '''
    Test if download_order() downloads data with overwrite flag
    set to false without pre-existing data.
    '''

    # Create mock HTTP response
    dl_url = TEST_URL + 'download/1?token=IAmAToken'
    order_description['_links']['results'] = [
        {'location': dl_url},
    ]

    get_url = TEST_URL + 'orders/v2/' + oid
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    downloaded_content = {'key': 'downloaded_file'}
    mock_resp = httpx.Response(
        HTTPStatus.OK,
        json=downloaded_content,
        headers={
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename="file.json"'
        })
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    # Download order and overwrite data
    _ = await cl.download_order(oid, directory=str(tmpdir), overwrite=False)

    assert json.loads(open(Path(tmpdir, 'file.json')).read()) != ...
    downloaded_content
