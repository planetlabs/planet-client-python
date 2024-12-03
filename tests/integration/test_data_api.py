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
from http import HTTPStatus
import hashlib
import json
import logging
import math
from pathlib import Path

import httpx
import pytest
import respx

from planet import exceptions, DataClient, data_filter
from planet.clients.data import (LIST_SORT_DEFAULT,
                                 LIST_SEARCH_TYPE_DEFAULT,
                                 SEARCH_SORT_DEFAULT)

TEST_URL = 'http://www.mocknotrealurl.com/api/path'
TEST_SEARCHES_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'

VALID_SEARCH_ID = '286469f0b27c476e96c3c4e561f59664'

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
@pytest.mark.anyio
async def test_search_basic(item_descriptions, search_response, session):

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
    items_list = [i async for i in cl.search(['PSScene'])]

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"], "filter": data_filter.empty_filter()
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.anyio
async def test_search_name(item_descriptions, search_response, session):

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
    items_list = [i async for i in cl.search(['PSScene'], name='quick_search')]

    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "filter": data_filter.empty_filter(),
        "name": "quick_search"
    }
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("geom_fixture", [('geom_geojson'),
                                          ('geom_reference')])
async def test_search_geometry(geom_fixture,
                               item_descriptions,
                               session,
                               request):

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
    geom = request.getfixturevalue(geom_fixture)
    items_list = [
        i async for i in cl.search(['PSScene'], name='quick_search',
                                   geometry=geom)
    ]
    # check that request is correct
    expected_request = {
        "item_types": ["PSScene"],
        "geometry": geom,
        "filter": data_filter.empty_filter(),
        "name": "quick_search"
    }
    actual_body = json.loads(respx.calls[0].request.content)

    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.anyio
async def test_search_filter(item_descriptions,
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
    items_list = [
        i async for i in cl.search(item_types=['PSScene'],
                                   search_filter=search_filter)
    ]

    # check that request is correct
    expected_request = {"item_types": ["PSScene"], "filter": search_filter}
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.anyio
async def test_search_filter_positional_args(item_descriptions,
                                             search_filter,
                                             search_response,
                                             session):
    """test the search method using positional args"""

    quick_search_url = f'{TEST_URL}/quick-search'

    item1, item2, item3 = item_descriptions
    response = {"features": [item1, item2, item3]}
    mock_resp = httpx.Response(HTTPStatus.OK, json=response)
    respx.post(quick_search_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)

    # search using a positional arg for the filter.
    items_list = [i async for i in cl.search(['PSScene'], search_filter)]

    # check that request is correct
    expected_request = {"item_types": ["PSScene"], "filter": search_filter}
    actual_body = json.loads(respx.calls[0].request.content)
    assert actual_body == expected_request

    # check that all of the items were returned unchanged
    assert items_list == item_descriptions


@respx.mock
@pytest.mark.anyio
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

    # run through the iterator to actually initiate the call
    [
        i async for i in cl.search(['PSScene'], search_filter=search_filter,
                                   sort=sort)
    ]


@respx.mock
@pytest.mark.anyio
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
    items_list = [
        i async for i in cl.search(['PSScene'], search_filter=search_filter,
                                   limit=2)
    ]

    # check only the first two results were returned
    assert items_list == item_descriptions[:2]


@respx.mock
@pytest.mark.anyio
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
    search = await cl.create_search(item_types=['PSScene'],
                                    search_filter=search_filter,
                                    name='test')

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
@pytest.mark.anyio
async def test_create_search_basic_positional_args(search_filter, session):
    """Test that positional arguments are accepted for create_search"""

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
    search = await cl.create_search(['PSScene'], search_filter, name='test')

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
@pytest.mark.anyio
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
    search = await cl.create_search(['PSScene'],
                                    search_filter=search_filter,
                                    name='test',
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
@pytest.mark.anyio
async def test_get_search_success(search_id, search_result, session):
    get_url = f'{TEST_SEARCHES_URL}/{search_id}'
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_result)
    respx.get(get_url).return_value = mock_resp
    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.get_search(search_id)
    assert search_result == search


@respx.mock
@pytest.mark.anyio
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
@pytest.mark.anyio
async def test_update_search_basic(search_filter, session):

    page_response = {
        "__daily_email_enabled": False,
        "_links": {
            "_self": "string", "thumbnail": "string"
        },
        "created": "2019-08-24T14:15:22Z",
        "filter": search_filter,
        "id": VALID_SEARCH_ID,
        "last_executed": "2019-08-24T14:15:22Z",
        "name": "test",
        "updated": "2019-08-24T14:15:22Z"
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.put(
        f'{TEST_SEARCHES_URL}/{VALID_SEARCH_ID}').return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.update_search(VALID_SEARCH_ID,
                                    item_types=['PSScene'],
                                    search_filter=search_filter,
                                    name='test')

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
@pytest.mark.anyio
async def test_update_search_basic_positional_args(search_filter, session):
    """Test that positional arguments are accepted for update_search"""

    page_response = {
        "__daily_email_enabled": False,
        "_links": {
            "_self": "string", "thumbnail": "string"
        },
        "created": "2019-08-24T14:15:22Z",
        "filter": search_filter,
        "id": VALID_SEARCH_ID,
        "last_executed": "2019-08-24T14:15:22Z",
        "name": "test",
        "updated": "2019-08-24T14:15:22Z"
    }
    mock_resp = httpx.Response(HTTPStatus.OK, json=page_response)
    respx.put(
        f'{TEST_SEARCHES_URL}/{VALID_SEARCH_ID}').return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    search = await cl.update_search(VALID_SEARCH_ID, ['PSScene'],
                                    search_filter,
                                    name='test')

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
@pytest.mark.anyio
@pytest.mark.parametrize("limit, expected_list_length", [(None, 4), (3, 3)])
async def test_list_searches_success(limit,
                                     expected_list_length,
                                     search_result,
                                     session):
    page1_response = {"_links": {}, "searches": [search_result] * 4}
    route = respx.get(TEST_SEARCHES_URL)
    route.return_value = httpx.Response(200, json=page1_response)

    cl = DataClient(session, base_url=TEST_URL)

    assert len([s async for s in cl.list_searches(limit=limit)
                ]) == expected_list_length

    assert route.called


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("sort, rel_url",
                         [(LIST_SORT_DEFAULT, ''),
                          ('created asc', '?_sort=created+asc')])
async def test_list_searches_sort(sort, rel_url, search_result, session):
    page1_response = {"_links": {}, "searches": [search_result] * 4}
    route = respx.get(f'{TEST_SEARCHES_URL}{rel_url}')
    route.return_value = httpx.Response(200, json=page1_response)

    cl = DataClient(session, base_url=TEST_URL)
    _ = [s async for s in cl.list_searches(sort=sort)]

    assert route.called


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("search_type, rel_url",
                         [(LIST_SEARCH_TYPE_DEFAULT, ''),
                          ('saved', '?search_type=saved')])
async def test_list_searches_searchtype(search_type,
                                        rel_url,
                                        search_result,
                                        session):
    page1_response = {"_links": {}, "searches": [search_result] * 4}
    route = respx.get(f'{TEST_SEARCHES_URL}{rel_url}')
    route.return_value = httpx.Response(200, json=page1_response)

    cl = DataClient(session, base_url=TEST_URL)
    _ = [s async for s in cl.list_searches(search_type=search_type)]

    assert route.called


@respx.mock
@pytest.mark.anyio
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
        [s async for s in cl.list_searches(sort=sort, search_type=search_type)]

    assert not route.called


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("retcode, expectation",
                         [(204, does_not_raise()),
                          (404, pytest.raises(exceptions.APIError))])
async def test_delete_search(retcode, expectation, session):
    mock_resp = httpx.Response(retcode)
    route = respx.delete(f'{TEST_SEARCHES_URL}/{VALID_SEARCH_ID}')
    route.return_value = mock_resp
    cl = DataClient(session, base_url=TEST_URL)

    with expectation:
        await cl.delete_search(VALID_SEARCH_ID)

    assert route.called


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("search_id, valid", [(VALID_SEARCH_ID, True),
                                              ('invalid', False)])
@pytest.mark.parametrize("limit, expected_count", [(None, 3), (2, 2)])
async def test_run_search_basic(item_descriptions,
                                session,
                                search_id,
                                valid,
                                limit,
                                expected_count):
    """Ensure run_search is successful and handles search_id and limit"""
    next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'
    item1, item2, item3 = item_descriptions
    page1_response = {
        "_links": {
            "_next": next_page_url
        }, "features": [item1, item2]
    }

    route = respx.get(f'{TEST_SEARCHES_URL}/{search_id}/results')
    route.return_value = httpx.Response(204, json=page1_response)

    page2_response = {"_links": {"_self": next_page_url}, "features": [item3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = DataClient(session, base_url=TEST_URL)

    if valid:
        items_list = [i async for i in cl.run_search(search_id, limit=limit)]

        assert route.called

        # check that all of the items were returned unchanged
        assert items_list == item_descriptions[:expected_count]
    else:
        with pytest.raises(exceptions.ClientError):
            [i async for i in cl.run_search(search_id)]


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("sort, rel_url, valid",
                         [(SEARCH_SORT_DEFAULT, '', True),
                          ('acquired asc', '?_sort=acquired+asc', True),
                          ('invalid', '', False)])
async def test_run_search_sort(item_descriptions,
                               session,
                               sort,
                               rel_url,
                               valid):
    next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'
    item1, item2, item3 = item_descriptions
    page1_response = {
        "_links": {
            "_next": next_page_url
        }, "features": [item1, item2]
    }

    route = respx.get(
        f'{TEST_SEARCHES_URL}/{VALID_SEARCH_ID}/results{rel_url}')
    route.return_value = httpx.Response(204, json=page1_response)

    page2_response = {"_links": {"_self": next_page_url}, "features": [item3]}
    mock_resp2 = httpx.Response(HTTPStatus.OK, json=page2_response)
    respx.get(next_page_url).return_value = mock_resp2

    cl = DataClient(session, base_url=TEST_URL)

    expectation = pytest.raises(
        exceptions.ClientError) if not valid else does_not_raise()

    with expectation:
        [s async for s in cl.run_search(VALID_SEARCH_ID, sort=sort)]
        assert route.called


@respx.mock
@pytest.mark.anyio
async def test_run_search_doesnotexist(session):
    route = respx.get(f'{TEST_SEARCHES_URL}/{VALID_SEARCH_ID}/results')
    route.return_value = httpx.Response(404)

    cl = DataClient(session, base_url=TEST_URL)
    with pytest.raises(exceptions.APIError):
        [i async for i in cl.run_search(VALID_SEARCH_ID)]

    assert route.called


@respx.mock
@pytest.mark.anyio
async def test_get_stats_success(search_filter, session):

    page_response = {
        "buckets": [
            {
                "count": 433638, "start_time": "2022-01-01T00:00:00.000000Z"
            },
            {
                "count": 431924, "start_time": "2022-01-02T00:00:00.000000Z"
            },
            {
                "count": 417138, "start_time": "2022-01-03T00:00:00.000000Z"
            },
        ],
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
@pytest.mark.anyio
async def test_get_stats_invalid_interval(search_filter, session):
    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await cl.get_stats(['PSScene'], search_filter, 'invalid')


@respx.mock
@pytest.mark.anyio
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
@pytest.mark.anyio
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
@pytest.mark.anyio
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
@pytest.mark.anyio
@pytest.mark.parametrize("status, expectation", [('inactive', True),
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
@pytest.mark.anyio
async def test_activate_asset_invalid_asset(session):
    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await cl.activate_asset({})


@respx.mock
@pytest.mark.anyio
async def test_wait_asset_success(session):
    asset_url = f'{TEST_URL}/asset'

    basic_udm2_asset = {
        "_links": {
            "_self": asset_url,
            "activate": "ACTIVATEURL",
            "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
        },
        "_permissions": ["download"],
        "md5_digest": None,
        "status": 'activating',
        "type": "basic_udm2"
    }

    basic_udm2_asset_active = copy.deepcopy(basic_udm2_asset)
    basic_udm2_asset_active['status'] = 'active'

    route = respx.get(asset_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=basic_udm2_asset),
        httpx.Response(HTTPStatus.OK, json=basic_udm2_asset),
        httpx.Response(HTTPStatus.OK, json=basic_udm2_asset_active)
    ]

    cl = DataClient(session, base_url=TEST_URL)
    asset = await cl.wait_asset(basic_udm2_asset, delay=0)

    assert asset == basic_udm2_asset_active


@respx.mock
@pytest.mark.anyio
async def test_wait_asset_max_attempts(session):
    asset_url = f'{TEST_URL}/asset'

    basic_udm2_asset = {
        "_links": {
            "_self": asset_url,
            "activate": "ACTIVATEURL",
            "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
        },
        "_permissions": ["download"],
        "md5_digest": None,
        "status": 'activating',
        "type": "basic_udm2"
    }

    route = respx.get(asset_url)
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=basic_udm2_asset),
        httpx.Response(HTTPStatus.OK, json=basic_udm2_asset),
    ]

    cl = DataClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await cl.wait_asset(basic_udm2_asset, delay=0, max_attempts=1)


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize("exists, overwrite",
                         [(False, False), (True, False), (True, True),
                          (False, True)])
async def test_download_asset(exists,
                              overwrite,
                              tmpdir,
                              open_test_img,
                              session):
    # NOTE: this is a slightly edited version of test_download_asset_img from
    # tests/integration/test_orders_api
    dl_url = f'{TEST_URL}/1?token=IAmAToken'

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

    basic_udm2_asset = {
        "_links": {
            "_self": "SELFURL",
            "activate": "ACTIVATEURL",
            "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
        },
        "_permissions": ["download"],
        "md5_digest": None,
        "status": 'active',
        "location": dl_url,
        "type": "basic_udm2"
    }

    cl = DataClient(session, base_url=TEST_URL)

    if exists:
        Path(tmpdir, 'img.tif').write_text('i exist')

    path = await cl.download_asset(basic_udm2_asset,
                                   directory=tmpdir,
                                   overwrite=overwrite)
    assert path.name == 'img.tif'
    assert path.is_file()

    if exists and not overwrite:
        assert path.read_text() == 'i exist'
    else:
        assert len(path.read_bytes()) == 527


@respx.mock
@pytest.mark.anyio
@pytest.mark.parametrize(
    "hashes_match, md5_entry, expectation",
    [(True, True, does_not_raise()),
     (False, True, pytest.raises(exceptions.ClientError)),
     (True, False, pytest.raises(exceptions.ClientError))])
async def test_validate_checksum(hashes_match, md5_entry, expectation, tmpdir):
    test_bytes = b'foo bar'
    testfile = Path(tmpdir / 'test.txt')
    testfile.write_bytes(test_bytes)

    hash_md5 = hashlib.md5(test_bytes).hexdigest()

    basic_udm2_asset = {
        "_links": {
            "_self": "SELFURL",
            "activate": "ACTIVATEURL",
            "type": "https://api.planet.com/data/v1/asset-types/basic_udm2"
        },
        "_permissions": ["download"],
        "status": 'active',
        "location": "DOWNLOADURL",
        "type": "basic_udm2"
    }

    if md5_entry:
        asset_hash = hash_md5 if hashes_match else 'invalid'
        basic_udm2_asset["md5_digest"] = asset_hash

    with expectation:
        DataClient.validate_checksum(basic_udm2_asset, testfile)
