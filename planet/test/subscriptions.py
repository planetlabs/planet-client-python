# Copyright 2021 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
import json

from datetime import datetime
from itertools import zip_longest

import respx

from httpx import Response
from respx.patterns import M

# M(url=TEST_URL) is case sensitive and matching a lower-case url, and it
# requires that there not be a '/'
TEST_URL = 'http://www.mocknotrealurl.com/api/path'

# Mock router representing an API that returns only a 500
# internal server error. The router is configured outside the test
# to help keep our test more readable.
failing_api_mock = respx.mock()
failing_api_mock.route(M(url__startswith=TEST_URL)).mock(
    return_value=Response(500, json={
        "code": 0, "message": "string"
    }))


def result_pages(status=None, size=40):
    """Helper for creating fake subscriptions listing pages."""
    all_subs = [{'id': str(i), 'status': 'running'} for i in range(1, 101)]
    select_subs = (sub for sub in all_subs
                   if not status or sub['status'] in status)
    pages = []
    for group in zip_longest(*[iter(select_subs)] * size):
        subs = list(sub for sub in group if sub is not None)
        page = {'subscriptions': subs, '_links': {}}
        pm = datetime.now().isoformat()
        if len(subs) == size:
            page['_links']['next'] = f'{TEST_URL}?pm={pm}'
        pages.append(page)
    return pages

# By default, respx's mock router asserts that all configured routes
# are followed in a test. Each of our parameterized tests follows only
# one route, so if we want to configure routes once and reuse them, we
# must disable the default.
mock_subscriptions_api = respx.mock(assert_all_called=False)

# 1. Request for status: running. Response has three pages.
mock_subscriptions_api.route(M(url=TEST_URL),
               M(params__contains={'status': 'running'})).mock(side_effect=[
                   Response(200, json=page)
                   for page in result_pages(status={'running'}, size=40)
               ])

# 2. Request for status: failed. Response has a single empty page.
mock_subscriptions_api.route(M(url=TEST_URL), M(params__contains={'status': 'failed'})).mock(
    side_effect=[Response(200, json={'subscriptions': []})])

# 3. Request for status: preparing. Response has a single empty page.
mock_subscriptions_api.route(M(url=TEST_URL),
               M(params__contains={'status': 'preparing'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 4. source_type: catalog requested. Response is the same as for 1.
mock_subscriptions_api.route(
    M(url=TEST_URL),
    M(params__contains={'source_type': 'catalog'})).mock(side_effect=[
        Response(200, json=page)
        for page in result_pages(status={'running'}, size=40)
    ])

# 5. source_type: soil_water_content requested. Response has a single empty page.
mock_subscriptions_api.route(M(url=TEST_URL),
               M(params__contains={'source_type': 'soil_water_content'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 6. No status or source_type requested. Response is the same as for 1.
mock_subscriptions_api.route(M(url=TEST_URL)).mock(
    side_effect=[Response(200, json=page) for page in result_pages(size=40)])


# The "creation", "update", and "cancel" mock APIs return submitted
# data to the caller. They are used to test methods that rely on POST,
# PATCH, or PUT.
def modify_response(request):
    if request.content:
        return Response(200, json=json.loads(request.content))
    else:
        return Response(200)


create_mock = respx.mock()
create_mock.route(M(url=TEST_URL),
                  method='POST').mock(side_effect=modify_response)

update_mock = respx.mock()
update_mock.route(M(url=f'{TEST_URL}/test'),
                  method='PUT').mock(side_effect=modify_response)

patch_mock = respx.mock()
patch_mock.route(M(url=f'{TEST_URL}/test'),
                 method='PATCH').mock(side_effect=modify_response)

cancel_mock = respx.mock()
cancel_mock.route(M(url=f'{TEST_URL}/test/cancel'),
                  method='POST').mock(side_effect=modify_response)

# Mock the subscription description API endpoint.
get_mock = respx.mock()
get_mock.route(
    M(url=f'{TEST_URL}/test'),
    method='GET').mock(return_value=Response(200,
                                             json={
                                                 'id': '42',
                                                 'name': 'test',
                                                 'delivery': 'yes, please',
                                                 'source': 'test'
                                             }))


def result_pages(status=None, size=40):
    """Helper for creating fake result listing pages."""
    all_results = [{'id': str(i), 'status': 'created'} for i in range(1, 101)]
    select_results = (result for result in all_results
                      if not status or result['status'] in status)
    pages = []
    for group in zip_longest(*[iter(select_results)] * size):
        results = list(result for result in group if result is not None)
        page = {'results': results, '_links': {}}
        pm = datetime.now().isoformat()
        if len(results) == size:
            url = f'{TEST_URL}/42/results?pm={pm}'
            page['_links']['next'] = url
        pages.append(page)
    return pages


# By default, respx's mock router asserts that all configured routes
# are followed in a test. Each of our parameterized tests follows only
# one route, so if we want to configure routes once and reuse them, we
# must disable the default.
res_api_mock = respx.mock(assert_all_called=False)

# 1. CSV results
res_api_mock.route(
    M(url__startswith=TEST_URL), M(params__contains={'format': 'csv'})).mock(
        side_effect=[Response(200, text="id,status\n1234-abcd,SUCCESS\n")])

# 2. Request for status: created. Response has three pages.
res_api_mock.route(
    M(url__startswith=TEST_URL),
    M(params__contains={'status': 'created'})).mock(side_effect=[
        Response(200, json=page)
        for page in result_pages(status={'created'}, size=40)
    ])

# 3. Request for status: queued. Response has a single empty page.
res_api_mock.route(M(url__startswith=TEST_URL),
                   M(params__contains={'status': 'queued'})).mock(
                       side_effect=[Response(200, json={'results': []})])

# 4. No status requested. Response is the same as for 1.
res_api_mock.route(M(url__startswith=TEST_URL)).mock(
    side_effect=[Response(200, json=page) for page in result_pages(size=40)])
