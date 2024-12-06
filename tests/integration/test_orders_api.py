# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
from contextlib import nullcontext as does_not_raise
import copy
import json
import hashlib
from http import HTTPStatus
import logging
import math
import os
from pathlib import Path
from unittest.mock import call, create_autospec

import httpx
import pytest
import respx

from planet import OrdersClient, exceptions, reporting
from planet.clients.orders import OrderStates

TEST_URL = 'http://www.MockNotRealURL.com/api/path'
TEST_BULK_CANCEL_URL = f'{TEST_URL}/bulk/orders/v2/cancel'
TEST_DOWNLOAD_URL = f'{TEST_URL}/download'
TEST_DOWNLOAD_ACTUAL_URL = f'{TEST_URL}/download_actual'
TEST_ORDERS_URL = f'{TEST_URL}/orders/v2'
TEST_STATS_URL = f'{TEST_URL}/stats/orders/v2'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def downloaded_content():
    return {'key': 'downloaded_file'}


@pytest.fixture
def original_content():
    return {'key': 'original_file'}


@pytest.fixture
def create_download_mock(downloaded_content, order_description, oid):
    """
    Mock an HTTP response for download.
    """

    def f():
        # Create mock HTTP response
        order_description['state'] = 'success'
        dl_url = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'
        order_description['_links']['results'] = [
            {
                'location': dl_url, 'name': 'file.json'
            },
        ]

        get_url = f'{TEST_ORDERS_URL}/{oid}'
        mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
        respx.get(get_url).return_value = mock_resp

        mock_resp = httpx.Response(HTTPStatus.OK,
                                   json=downloaded_content,
                                   headers={
                                       'Content-Type':
                                       'application/json',
                                       'Content-Disposition':
                                       'attachment; filename="file.json"'
                                   })
        respx.get(dl_url).return_value = mock_resp

    return f


def test_OrderStates_reached():
    assert not OrderStates.reached('running', 'queued')
    assert OrderStates.reached('running', 'running')
    assert OrderStates.reached('running', 'failed')


def test_OrderStates_passed():
    assert not OrderStates.reached('running', 'queued')
    assert not OrderStates.passed('running', 'running')
    assert OrderStates.passed('running', 'success')


@respx.mock
@pytest.mark.anyio
async def test_list_orders_basic(order_descriptions, session):
    next_page_url = TEST_ORDERS_URL + 'blob/?page_marker=IAmATest'

    order1, order2, order3 = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string", "next": next_page_url
        },
        "orders": [order1, order2]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    page2_response = {"_links": {"_self": next_page_url}, "orders": [order3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = OrdersClient(session, base_url=TEST_URL)
    assert order_descriptions == [o async for o in cl.list_orders()]


@respx.mock
@pytest.mark.anyio
async def test_list_orders_filtering_and_sorting(order_descriptions, session):
    list_url = TEST_ORDERS_URL + '?source_type=all&state=failed&name=my_order_xyz&name__contains=xyz&created_on=2018-02-12T00:00:00Z/..&last_modified=../2018-03-18T12:31:12Z&hosting=true&sort_by=name DESC'

    order1, order2, _ = order_descriptions

    page1_response = {
        "_links": {
            "_self": "string"
        }, "orders": [order1, order2]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(list_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    # if the value of each arg doesn't get sent as a url parameter,
    # the mock will fail and this test will fail
    assert [order1, order2] == [
        o async for o in cl.list_orders(
            state='failed', name='my_order_xyz', name__contains='xyz',
            created_on='2018-02-12T00:00:00Z/..',
            last_modified='../2018-03-18T12:31:12Z', hosting=True,
            sort_by='name DESC')
    ]


@pytest.mark.anyio
async def test_list_orders_state_invalid(session):
    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        [o async for o in cl.list_orders(state='invalidstate')]


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("limit,limited_list_length", [(None, 100), (0, 102),
                                                       (1, 1)])
async def test_list_orders_limit(order_descriptions,
                                 session,
                                 limit,
                                 limited_list_length):
    nono_page_url = None

    # Creating 102 (3x34) order descriptions
    long_order_descriptions = order_descriptions * 34

    all_orders = {}
    for x in range(1, len(long_order_descriptions) + 1):
        all_orders["order{0}".format(x)] = long_order_descriptions[x - 1]

    page1_response = {
        "_links": {
            "_self": "string", "next": nono_page_url
        },
        "orders": [
            all_orders['order%s' % num]
            for num in range(1, limited_list_length + 1)
        ]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    assert len([o async for o in cl.list_orders(limit=limit)
                ]) == limited_list_length


@respx.mock
@pytest.mark.anyio
async def test_create_order_basic(oid,
                                  order_description,
                                  order_request,
                                  session):
    route = respx.post(TEST_ORDERS_URL)
    route.return_value = httpx.Response(HTTPStatus.OK, json=order_description)

    cl = OrdersClient(session, base_url=TEST_URL)
    order = await cl.create_order(order_request)

    assert order == order_description

    assert json.loads(route.calls.last.request.content) == order_request


@respx.mock
@pytest.mark.anyio
async def test_create_order_bad_item_type(order_request, session):
    resp = {
        "field": {
            "Products": [{
                "message":
                "Bad item type 'invalid' for bundle type 'analytic'"
            }]
        },
        "general": [{
            "message": "Unable to accept order"
        }]
    }
    mock_resp = httpx.Response(400, json=resp)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp
    order_request['products'][0]['item_type'] = 'invalid'
    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.BadQuery):
        await cl.create_order(order_request)


@respx.mock
@pytest.mark.anyio
async def test_create_order_item_id_does_not_exist(order_request, session):
    resp = {
        "field": {
            "Details": [{
                "message": ("Item ID 4500474_2133707_2021-05-20_2419 / " +
                            "Item Type PSScene3Band doesn't exist")
            }]
        },
        "general": [{
            "message": "Unable to accept order"
        }]
    }
    mock_resp = httpx.Response(400, json=resp)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp
    order_request['products'][0]['item_ids'] = \
        '4500474_2133707_2021-05-20_2419'
    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.BadQuery):
        await cl.create_order(order_request)


@respx.mock
@pytest.mark.anyio
async def test_get_order(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    order = await cl.get_order(oid)
    assert order_description == order


@pytest.mark.anyio
async def test_get_order_invalid_id(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.get_order('-')


@respx.mock
@pytest.mark.anyio
async def test_get_order_id_doesnt_exist(oid, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    resp = {"message": f'Could not load order ID: {oid}'}
    mock_resp = httpx.Response(404, json=resp)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.MissingResource):
        await cl.get_order(oid)


@respx.mock
@pytest.mark.anyio
async def test_cancel_order(oid, order_description, session):
    cancel_url = f'{TEST_ORDERS_URL}/{oid}'
    order_description['state'] = 'cancelled'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    example_resp = mock_resp.json()
    respx.put(cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    json_resp = await cl.cancel_order(oid)
    assert json_resp == example_resp


@pytest.mark.anyio
async def test_cancel_order_invalid_id(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.cancel_order('invalid_order_id')


@respx.mock
@pytest.mark.anyio
async def test_cancel_order_id_doesnt_exist(oid, session):
    cancel_url = f'{TEST_ORDERS_URL}/{oid}'

    resp = {"message": f'No such order ID: {oid}.'}
    mock_resp = httpx.Response(404, json=resp)
    respx.put(cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.MissingResource):
        await cl.cancel_order(oid)


@respx.mock
@pytest.mark.anyio
async def test_cancel_order_id_cannot_be_cancelled(oid, session):
    cancel_url = f'{TEST_ORDERS_URL}/{oid}'

    resp = {"message": 'Order not in a cancellable state'}
    mock_resp = httpx.Response(409, json=resp)
    respx.put(cancel_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.Conflict):
        await cl.cancel_order(oid)


@respx.mock
@pytest.mark.anyio
async def test_cancel_orders_by_ids(session, oid):
    oid2 = '5ece1dc0-ea81-11eb-837c-acde48001122'
    test_ids = [oid, oid2]
    example_result = {
        "result": {
            "succeeded": {
                "count": 1
            },
            "failed": {
                "count":
                1,
                "failures": [{
                    "order_id": oid2,
                    "message": "Order not in a cancellable state",
                }]
            }
        }
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_result)
    respx.post(TEST_BULK_CANCEL_URL).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.cancel_orders(test_ids)

    assert res == example_result

    expected_body = {"order_ids": test_ids}
    actual_body = json.loads(respx.calls.last.request.content)
    assert actual_body == expected_body


@pytest.mark.anyio
async def test_cancel_orders_by_ids_invalid_id(session, oid):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        _ = await cl.cancel_orders([oid, "invalid_oid"])


@respx.mock
@pytest.mark.anyio
async def test_cancel_orders_all(session):
    example_result = {
        "result": {
            "succeeded": {
                "count": 2
            }, "failed": {
                "count": 0, "failures": []
            }
        }
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_result)
    respx.post(TEST_BULK_CANCEL_URL).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.cancel_orders()

    assert res == example_result

    actual_body = json.loads(respx.calls.last.request.content)
    assert actual_body == {}


@respx.mock
@pytest.mark.anyio
async def test_wait_default(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'running'
    order_description3 = copy.deepcopy(order_description)
    order_description3['state'] = 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2),
        httpx.Response(HTTPStatus.OK, json=order_description3)
    ]

    cl = OrdersClient(session, base_url=TEST_URL)
    state = await cl.wait(oid, delay=0)
    assert state == 'success'


@respx.mock
@pytest.mark.anyio
async def test_wait_callback(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'running'
    order_description3 = copy.deepcopy(order_description)
    order_description3['state'] = 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2),
        httpx.Response(HTTPStatus.OK, json=order_description3)
    ]

    mock_bar = create_autospec(reporting.StateBar)
    mock_callback = mock_bar.update_state

    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.wait(oid, delay=0, callback=mock_callback)

    # check state was sent to callback as expected
    expected = [call(s) for s in ['queued', 'running', 'success']]
    mock_callback.assert_has_calls(expected)


@respx.mock
@pytest.mark.anyio
async def test_wait_state(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    order_description2 = copy.deepcopy(order_description)
    order_description2['state'] = 'running'
    order_description3 = copy.deepcopy(order_description)
    order_description3['state'] = 'success'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
        httpx.Response(HTTPStatus.OK, json=order_description2),
        httpx.Response(HTTPStatus.OK, json=order_description3)
    ]

    cl = OrdersClient(session, base_url=TEST_URL)
    state = await cl.wait(oid, state='running', delay=0)
    assert state == 'running'


@respx.mock
@pytest.mark.anyio
async def test_wait_max_attempts_enabled(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
    ]

    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.wait(oid, max_attempts=1, delay=0)


@respx.mock
@pytest.mark.anyio
async def test_wait_max_attempts_disabled(oid, order_description, session):
    get_url = f'{TEST_ORDERS_URL}/{oid}'

    route = respx.get(get_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=order_description),
    ] * 300

    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(RuntimeError):
        # falls off the end of the mocked responses
        await cl.wait(oid, max_attempts=0, delay=0)


@pytest.mark.anyio
async def test_wait_invalid_oid(session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.wait("invalid_oid", delay=0)


@pytest.mark.anyio
async def test_wait_invalid_state(oid, session):
    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.wait(oid, state="invalid_state", delay=0)


@respx.mock
@pytest.mark.anyio
async def test_aggegated_order_stats(session):
    example_stats = {
        "organization": {
            "queued_orders": 0, "running_orders": 6
        },
        "user": {
            "queued_orders": 0, "running_orders": 0
        }
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=example_stats)
    respx.get(TEST_STATS_URL).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    res = await cl.aggregated_order_stats()

    assert res == example_stats


@respx.mock
@pytest.mark.anyio
async def test_download_asset_md(tmpdir, session):
    dl_url = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'

    md_json = {'key': 'value'}
    md_headers = {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="metadata.json"'
    }

    mock_redirect = httpx.Response(HTTPStatus.FOUND,
                                   headers={
                                       'Location': TEST_DOWNLOAD_ACTUAL_URL,
                                       'Content-Length': '0'
                                   })
    mock_resp = httpx.Response(HTTPStatus.OK, json=md_json, headers=md_headers)

    respx.get(dl_url).return_value = mock_redirect
    respx.get(TEST_DOWNLOAD_ACTUAL_URL).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    filename = await cl.download_asset(dl_url, directory=str(tmpdir))

    with open(filename) as f:
        assert json.load(f) == {'key': 'value'}

    assert Path(filename).name == 'metadata.json'


@respx.mock
@pytest.mark.anyio
async def test_download_asset_img(tmpdir, open_test_img, session):
    dl_url = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'

    img_headers = {
        'Content-Type': 'image/tiff',
        'Content-Length': '527',
        'Content-Disposition': 'attachment; filename="img.tif"'
    }

    async def _stream_img():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v) / (chunksize))):
            yield v[i * chunksize:min((i + 1) * chunksize, len(v))]

    # populate request parameter to avoid respx cloning, which throws
    # an error caused by respx and not this code
    # https://github.com/lundberg/respx/issues/130
    mock_resp = httpx.Response(HTTPStatus.OK,
                               stream=_stream_img(),
                               headers=img_headers,
                               request='donotcloneme')
    respx.get(dl_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    filename = await cl.download_asset(dl_url, directory=str(tmpdir))

    assert Path(filename).name == 'img.tif'
    assert os.path.isfile(filename)


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("checksum", [("MD5"), ("SHA256")])
@pytest.mark.parametrize(
    "asset1_bytes, expectation",
    [(b"1", does_not_raise()), (b"1", does_not_raise()),
     (b"does not match", pytest.raises(exceptions.ClientError))])
async def test_validate_checksum_checksum(tmpdir,
                                          asset1_bytes,
                                          expectation,
                                          checksum):

    itemtype1_dir = Path(tmpdir, 'itemtype1')
    itemtype1_dir.mkdir()

    asset1 = itemtype1_dir / 'asset1.tif'
    asset1.write_bytes(b"1")

    asset2 = itemtype1_dir / 'asset2.json'
    asset2.write_bytes(b'{"foo": "bar"}')
    asset2_bytes = asset2.read_bytes()

    manifest_data = {
        "name": "",
        "files": [
            {
                "path": "itemtype1/asset1.tif",
                "digests": {
                    "md5": hashlib.md5(asset1_bytes).hexdigest(),
                    "sha256": hashlib.sha256(asset1_bytes).hexdigest()}
            }, {
                "path": "itemtype1/asset2.json",
                "digests": {
                    "md5": hashlib.md5(asset2_bytes).hexdigest(),
                    "sha256": hashlib.sha256(asset2_bytes).hexdigest()}
            }]
    }  # yapf: disable
    Path(tmpdir, 'manifest.json').write_text(json.dumps(manifest_data))

    with expectation:
        OrdersClient.validate_checksum(Path(tmpdir), checksum)


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize(
    "create, corrupt, expectation",
    [(True, False, does_not_raise()),
     (True, True, pytest.raises(exceptions.ClientError)),
     (False, False, pytest.raises(exceptions.ClientError))])
async def test_validate_checksum_manifest(
    tmpdir,
    create,
    corrupt,
    expectation,
):
    itemtype1_dir = Path(tmpdir, 'itemtype1')
    itemtype1_dir.mkdir()

    asset1 = itemtype1_dir / 'asset1.tif'
    asset1.write_bytes(b"1")

    Path(tmpdir, 'asset1.tif').write_bytes(b"1")

    manifest_data = {
        "name":
        "",
        "files": [{
            "path": "itemtype1/asset1.tif",
            "digests": {
                "md5": hashlib.md5(b"1").hexdigest(),
                "sha256": hashlib.sha256(b"1").hexdigest()
            },
        }]
    }
    if create:
        if corrupt:
            Path(tmpdir, 'manifest.json').write_text('not json')
        else:
            Path(tmpdir, 'manifest.json').write_text(json.dumps(manifest_data))

    with expectation:
        OrdersClient.validate_checksum(Path(tmpdir), 'md5')


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize(
    "results, paths",
    [(None, []),
     ([], []),
     ([{"location": f'{TEST_DOWNLOAD_URL}/1',
        "name": "oid/itemtype1/asset.json"},
       {"location": f'{TEST_DOWNLOAD_URL}/2',
        "name": "oid/itemtype2/asset.json"},
       ],
      [Path('oid', 'itemtype1', 'asset.json'),
       Path('oid', 'itemtype2', 'asset.json'),
       ])
     ])  # yapf: disable
async def test_download_order_success(results,
                                      paths,
                                      tmpdir,
                                      order_description,
                                      oid,
                                      session):

    # Mock an HTTP response for download
    order_description['state'] = 'success'
    order_description['_links']['results'] = results

    get_url = f'{TEST_ORDERS_URL}/{oid}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    mock_resp1 = httpx.Response(HTTPStatus.OK,
                                json={'key': 'value'},
                                headers={
                                    'Content-Type':
                                    'application/json',
                                    'Content-Disposition':
                                    'attachment; filename="asset.json"'
                                })
    respx.get(f'{TEST_DOWNLOAD_URL}/1').return_value = mock_resp1

    mock_resp2 = httpx.Response(HTTPStatus.OK,
                                json={'key2': 'value2'},
                                headers={
                                    'Content-Type':
                                    'application/json',
                                    'Content-Disposition':
                                    'attachment; filename="asset.json"'
                                })
    respx.get(f'{TEST_DOWNLOAD_URL}/2').return_value = mock_resp2

    cl = OrdersClient(session, base_url=TEST_URL)
    filenames = await cl.download_order(oid, directory=str(tmpdir))

    assert filenames == [Path(tmpdir, p) for p in paths]

    if filenames:
        with open(filenames[0]) as f:
            assert json.load(f) == {'key': 'value'}

        with open(filenames[1]) as f:
            assert json.load(f) == {'key2': 'value2'}


@respx.mock
@pytest.mark.anyio
async def test_download_order_state(tmpdir, order_description, oid, session):
    dl_url1 = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'
    order_description['_links']['results'] = [
        {
            'location': dl_url1
        },
    ]

    get_url = f'{TEST_ORDERS_URL}/{oid}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
    respx.get(get_url).return_value = mock_resp

    cl = OrdersClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.ClientError):
        await cl.download_order(oid, directory=str(tmpdir))


@respx.mock
@pytest.mark.anyio
async def test_download_order_overwrite_true_preexisting_data(
        tmpdir,
        oid,
        session,
        create_download_mock,
        original_content,
        downloaded_content):
    """
    Test if download_order() overwrites pre-existing data with
    overwrite flag set to True.
    """

    # Save JSON to a temporary file
    with open(Path(tmpdir, 'file.json'), "a") as out_file:
        json.dump(original_content, out_file)

    create_download_mock()
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.download_order(oid, directory=str(tmpdir), overwrite=True)

    # Check that the data downloaded has overwritten the original data
    with open(Path(tmpdir, 'file.json')) as f:
        assert json.load(f) == downloaded_content


@respx.mock
@pytest.mark.anyio
async def test_download_order_overwrite_false_preexisting_data(
        tmpdir, oid, session, create_download_mock, original_content):
    """
    Test if download_order() does not overwrite pre-existing
    data with overwrite flag set to False.
    """

    # Save JSON to a temporary file
    with open(Path(tmpdir, 'file.json'), "a") as out_file:
        json.dump(original_content, out_file)

    create_download_mock()
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.download_order(oid, directory=str(tmpdir), overwrite=False)

    # Check that the original data has not been overwritten
    with open(Path(tmpdir, 'file.json')) as f:
        assert json.load(f) == original_content


@respx.mock
@pytest.mark.anyio
async def test_download_order_overwrite_true_nonexisting_data(
        tmpdir, oid, session, create_download_mock, downloaded_content):
    """
    Test if download_order() downloads data with overwrite flag
    set to true without pre-existing data.
    """

    create_download_mock()
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.download_order(oid, directory=str(tmpdir), overwrite=True)

    with open(Path(tmpdir, 'file.json')) as f:
        assert json.load(f) == downloaded_content


@respx.mock
@pytest.mark.anyio
async def test_download_order_overwrite_false_nonexisting_data(
        tmpdir, oid, session, create_download_mock, downloaded_content):
    """
    Test if download_order() downloads data with overwrite flag
    set to false without pre-existing data.
    """

    create_download_mock()
    cl = OrdersClient(session, base_url=TEST_URL)
    await cl.download_order(oid, directory=str(tmpdir), overwrite=False)

    # Check that the was data downloaded and has the correct contents
    with open(Path(tmpdir, 'file.json')) as f:
        assert json.load(f) == downloaded_content
