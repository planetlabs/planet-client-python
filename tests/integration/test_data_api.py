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
from http import HTTPStatus
import json
import logging

import httpx
import pytest
import respx

from planet import exceptions, DataClient

TEST_URL = 'http://www.MockNotRealURL.com/api/path'
TEST_SEARCHES_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def search_filter(get_test_file_json):
    filename = 'data_search_filter_2022-01.json'
    return get_test_file_json(filename)


@pytest.fixture
def item_descriptions(get_test_file_json):
    item_ids = [
        '20220125_075509_67_1061',
        '20220125_075511_17_1061',
        '20220125_075650_17_1061'
    ]
    items = [get_test_file_json(f'data_item_{id}.json') for id in item_ids]
    return items


@pytest.fixture
def search_response(item_descriptions):
    response = {
        "type": "FeatureCollection",
        "_links": {
            "_first": "firstpageurl",
            "_next": "nextpageurl",
            "_self": "selfurl"
        },
        "features": item_descriptions
    }

    return response


@respx.mock
@pytest.mark.asyncio
async def test_search_basic(item_descriptions,
                            search_filter,
                            search_response,
                            session):

    quick_search_url = f'{TEST_URL}/quick-search'
    next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'

    item1, item2, item3 = item_descriptions
    page1_response = {
        "_links": {
            "_next": next_page_url
        }, "features": [item1, item2]
    }
    mock_resp1 = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.post(quick_search_url).return_value = mock_resp1

    page2_response = {"_links": {"_self": next_page_url}, "features": [item3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = DataClient(session, base_url=TEST_URL)
    items = await cl.search(['PSScene'], search_filter, name='quick_search')
    items_list = [i async for i in items]

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "filter": search_filter,
        "name": "quick_search"
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.asyncio
async def test_search_sort(item_descriptions,
                           search_filter,
                           search_response,
                           session):

    sort = 'acquired asc'
    quick_search_url = f'{TEST_URL}/quick-search?_sort={sort}'

    item1, _, _ = item_descriptions
    page1_response = {"_links": {}, "features": [item1]}
    mock_resp1 = httpx.Response(HTTPStatus.OK, json=page1_response)
    respx.post(quick_search_url).return_value = mock_resp1

    # if the sort parameter is not used correctly, the client will not send
    # the request to the mocked endpoint and this test will fail
    cl = DataClient(session, base_url=TEST_URL)
    items = await cl.search(['PSScene'], search_filter, sort=sort)

    # run through the iterator to actually initiate the call
    [i async for i in items]


@respx.mock
@pytest.mark.asyncio
async def test_search_limit(item_descriptions,
                            search_filter,
                            search_response,
                            session):

    quick_search_url = f'{TEST_URL}/quick-search'

    page_response = {
        "_links": {},
        "features": item_descriptions  # three items
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.post(quick_search_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    items = await cl.search(['PSScene'], search_filter, limit=2)
    items_list = [i async for i in items]

    # check only the first two results were returned
    assert items_list == item_descriptions[:2]


@respx.mock
@pytest.mark.asyncio
async def test_create_search_basic(search_filter, session):

    page_response = {
        "__daily_email_enabled": False,
        "_links": {
            "_self": "string", "thumbnail": "string"
        },
        "created": "2019-08-24T14:15:22Z",
        "filter": search_filter,
        "id": "string",
        "last_executed": "2019-08-24T14:15:22Z",
        "name": "test",
        "updated": "2019-08-24T14:15:22Z"
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.post(TEST_SEARCHES_URL).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.create_search('test', ['PSScene'], search_filter)

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "filter": search_filter,
        "name": "test",
        "__daily_email_enabled": False
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check the response is returned unaltered
    assert search == page_response


@respx.mock
@pytest.mark.asyncio
async def test_create_search_email(search_filter, session):

    page_response = {
        "__daily_email_enabled": True,
        "_links": {
            "_self": "string", "thumbnail": "string"
        },
        "created": "2019-08-24T14:15:22Z",
        "filter": search_filter,
        "id": "string",
        "last_executed": "2019-08-24T14:15:22Z",
        "name": "test",
        "updated": "2019-08-24T14:15:22Z"
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.post(TEST_SEARCHES_URL).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.create_search('test', ['PSScene'],
                                    search_filter,
                                    enable_email=True)

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "filter": search_filter,
        "name": "test",
        "__daily_email_enabled": True
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check the response is returned unaltered
    assert search == page_response


@respx.mock
@pytest.mark.asyncio
async def test_get_search_success(search_id, search_result, session):
    get_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_result)
    respx.get(get_url).return_value = mock_resp
    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.get_search(search_id)
    assert search_result == search


@respx.mock
@pytest.mark.asyncio
async def test_get_search_id_doesnt_exist(search_id, session):
    get_url = f'{TEST_SEARCHES_URL}/{search_id}'

    resp = {
        "message": f'The requested search id does not exist:\
        {search_id}'
    }
    mock_resp = httpx.Response(404, json=resp)
    respx.get(get_url).return_value = mock_resp
    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.MissingResource):
        await cl.get_search(search_id)


@respx.mock
@pytest.mark.asyncio
async def test_update_search_basic(search_filter, session):
    sid = 'search_id'

    page_response = {
        "__daily_email_enabled": False,
        "_links": {
            "_self": "string", "thumbnail": "string"
        },
        "created": "2019-08-24T14:15:22Z",
        "filter": search_filter,
        "id": sid,
        "last_executed": "2019-08-24T14:15:22Z",
        "name": "test",
        "updated": "2019-08-24T14:15:22Z"
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.put(f'{TEST_SEARCHES_URL}/{sid}').return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.update_search(sid, 'test', ['PSScene'], search_filter)

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "filter": search_filter,
        "name": "test",
        "__daily_email_enabled": False
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check the response is returned unaltered
    assert search == page_response


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("limit, expected_list_length", [(None, 4), (3, 3)])
async def test_list_searches_success(limit,
                                     expected_list_length,
                                     search_result,
                                     session):
    page1_response = {"_links": {}, "searches": [search_result] * 4}
    route = respx.get(TEST_SEARCHES_URL)
    route.return_value = httpx.Response(200, json=page1_response)

    cl = DataClient(session, base_url=TEST_URL)

    searches = await cl.list_searches(limit=limit)
    searches_list_length = len([s async for s in searches])
    assert searches_list_length == expected_list_length

    assert route.called


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sort, search_type, expectation",
    [('DOESNOTEXIST', 'ANY', pytest.raises(exceptions.ClientError)),
     ('CREATED DESC', 'DOESNOTEXIST', pytest.raises(exceptions.ClientError))])
async def test_list_searches_args_do_not_match(sort,
                                               search_type,
                                               expectation,
                                               session):
    route = respx.get(TEST_SEARCHES_URL)
    route.return_value = httpx.Response(200, json={})

    cl = DataClient(session, base_url=TEST_URL)

    with expectation:
        await cl.list_searches(sort=sort, search_type=search_type)

    assert not route.called


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("retcode, expectation",
                         [(204, does_not_raise()),
                          (404, pytest.raises(exceptions.APIError))])
async def test_delete_search(retcode, expectation, session):
    sid = 'search_id'
    mock_resp = httpx.Response(retcode)
    route = respx.delete(f'{TEST_SEARCHES_URL}/{sid}')
    route.return_value = mock_resp
    cl = DataClient(session, base_url=TEST_URL)

    with expectation:
        await cl.delete_search(sid)

    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_run_search_success(item_descriptions, session):
    sid = 'search_id'
    route = respx.get(f'{TEST_SEARCHES_URL}/{sid}/results')

    next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'
    item1, item2, item3 = item_descriptions
    page1_response = {
        "_links": {
            "_next": next_page_url
        }, "features": [item1, item2]
    }

    route.return_value = httpx.Response(204, json=page1_response)

    page2_response = {"_links": {"_self": next_page_url}, "features": [item3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = DataClient(session, base_url=TEST_URL)
    items = await cl.run_search(sid)
    items_list = [i async for i in items]

    assert route.called

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.asyncio
async def test_run_search_doesnotexist(session):
    sid = 'search_id'
    route = respx.get(f'{TEST_SEARCHES_URL}/{sid}/results')
    route.return_value = httpx.Response(404)

    cl = DataClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.APIError):
        items = await cl.run_search(sid)
        # this won't throw the error until the iterator is processed
        # issue 476
        [i async for i in items]

    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_get_stats_success(search_filter, session):

    page_response = {
        "buckets": [{
            "count": 433638, "start_time": "2022-01-01T00:00:00.000000Z"
        },
                    {
                        "count": 431924,
                        "start_time": "2022-01-02T00:00:00.000000Z"
                    },
                    {
                        "count": 417138,
                        "start_time": "2022-01-03T00:00:00.000000Z"
                    }]
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.post(TEST_STATS_URL).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    stats = await cl.get_stats(['PSScene'], search_filter, 'day')

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"], "filter": search_filter, "interval": "day"
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check the response is returned unaltered
    assert stats == page_response


@respx.mock
@pytest.mark.asyncio
async def test_get_stats_invalid_interval(search_filter, session):
    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await cl.get_stats(['PSScene'], search_filter, 'invalid')


@respx.mock
@pytest.mark.asyncio
async def test_list_item_assets_success(session):
    item_type_id = 'PSScene'
    item_id = '20221003_002705_38_2461'
    assets_url = f'{TEST_URL}/item-types/{item_type_id}/items/{item_id}/assets'

    page_response = {
        "basic_analytic_4b": {
            "_links": {
                "_self":
                "SELFURL",
                "activate":
                "ACTIVATEURL",
                "type":
                "https://api.planet.com/data/v1/asset-types/basic_analytic_4b"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": "inactive",
            "type": "basic_analytic_4b"
        },
        "basic_udm2": {
            "_links": {
                "_self": "SELFURL",
                "activate": "ACTIVATEURL",
                "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": "inactive",
            "type": "basic_udm2"
        }
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.get(assets_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    assets = await cl.list_item_assets(item_type_id, item_id)

    # check the response is returned unaltered
    assert assets == page_response


@respx.mock
@pytest.mark.asyncio
async def test_list_item_assets_missing(session):
    item_type_id = 'PSScene'
    item_id = '20221003_002705_38_2461xx'
    assets_url = f'{TEST_URL}/item-types/{item_type_id}/items/{item_id}/assets'

    mock_resp = httpx.Response(404)
    respx.get(assets_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.APIError):
        await cl.list_item_assets(item_type_id, item_id)


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("asset_type_id, expectation",
                         [('basic_udm2', does_not_raise()),
                          ('invalid', pytest.raises(exceptions.ClientError))])
async def test_get_asset(asset_type_id, expectation, session):
    item_type_id = 'PSScene'
    item_id = '20221003_002705_38_2461'
    assets_url = f'{TEST_URL}/item-types/{item_type_id}/items/{item_id}/assets'

    basic_udm2_asset = {
            "_links": {
                "_self": "SELFURL",
                "activate": "ACTIVATEURL",
                "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": "inactive",
            "type": "basic_udm2"
        }

    page_response = {
        "basic_analytic_4b": {
            "_links": {
                "_self":
                "SELFURL",
                "activate":
                "ACTIVATEURL",
                "type":
                "https://api.planet.com/data/v1/asset-types/basic_analytic_4b"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": "inactive",
            "type": "basic_analytic_4b"
        },
        "basic_udm2": basic_udm2_asset
    }

    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.get(assets_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)

    with expectation:
        asset = await cl.get_asset(item_type_id, item_id, asset_type_id)
        assert asset == basic_udm2_asset


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("status, expectation",
                         [('inactive', True),
                          ('active', False)])
async def test_activate_asset_success(status, expectation, session):
    activate_url = f'{TEST_URL}/activate'

    mock_resp = httpx.Response(HTTPStatus.OK)
    route = respx.get(activate_url)
    route.return_value = mock_resp

    basic_udm2_asset = {
            "_links": {
                "_self": "SELFURL",
                "activate": activate_url,
                "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
            },
            "_permissions": ["download"],
            "md5_digest": None,
            "status": status,
            "type": "basic_udm2"
        }

    cl = DataClient(session, base_url=TEST_URL)
    await cl.activate_asset(basic_udm2_asset)

    assert route.called == expectation


@respx.mock
@pytest.mark.asyncio
async def test_activate_asset_invalid_asset(session):
    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await cl.activate_asset({})


@respx.mock
@pytest.mark.asyncio
async def test_wait_asset_success(session):
    cl = DataClient(session, base_url=TEST_URL)

    raise NotImplementedError


@respx.mock
@pytest.mark.asyncio
async def test_download_asset_success(session):
    cl = DataClient(session, base_url=TEST_URL)

    raise NotImplementedError
