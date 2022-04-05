# Copyright 2022 Planet Labs, PBC.
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
from http import HTTPStatus
import logging

import httpx
import pytest
import respx

from planet import DataClient

TEST_URL = 'http://www.MockNotRealURL.com/api/path'
TEST_SEARCH_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def search_filter(get_test_file_json):
    filename = 'search_filter_2022_01.json'
    return get_test_file_json(filename)


@pytest.fixture
def quick_search_request(search_filter):
    return {"item_types": ["PSScene"], "filter": search_filter}


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
async def test_quick_search_success(item_descriptions,
                                    quick_search_filter,
                                    quick_search_request,
                                    search_response,
                                    session):

    quick_search_url = f'{TEST_URL}/quick-search'
    mock_resp = httpx.Response(HTTPStatus.OK, json=search_response)
    respx.post(quick_search_url).return_value = mock_resp

    cl = DataClient(session, base_url=TEST_URL)
    items = list(await cl.quick_search('PSScene', quick_search_filter))

    assert mock_resp.called_once_with(quick_search_request)
    assert items == item_descriptions
