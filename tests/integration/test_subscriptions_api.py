"""Tests of the Planet Subscriptions API client."""

import csv
from datetime import datetime
from itertools import zip_longest
import json

from httpx import Response
import pytest
import respx
from respx.patterns import M

from planet.clients.subscriptions import SubscriptionsClient
from planet.exceptions import APIError, PagingError, ServerError
from planet.http import Session

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


def subscription_pages(status=None, size=40):
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
api_mock = respx.mock(assert_all_called=False)

# 1. Request for status: running. Response has three pages.
api_mock.route(M(url=TEST_URL),
               M(params__contains={'status': 'running'})).mock(side_effect=[
                   Response(200, json=page)
                   for page in subscription_pages(status={'running'}, size=40)
               ])

# 2. Request for status: failed. Response has a single empty page.
api_mock.route(M(url=TEST_URL), M(params__contains={'status': 'failed'})).mock(
    side_effect=[Response(200, json={'subscriptions': []})])

# 3. Request for status: preparing. Response has a single empty page.
api_mock.route(M(url=TEST_URL),
               M(params__contains={'status': 'preparing'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 4. source_type: catalog requested. Response is the same as for 1.
api_mock.route(
    M(url=TEST_URL),
    M(params__contains={'source_type': 'catalog'})).mock(side_effect=[
        Response(200, json=page)
        for page in subscription_pages(status={'running'}, size=40)
    ])

# 5. source_type: soil_water_content requested. Response has a single empty page.
api_mock.route(M(url=TEST_URL),
               M(params__contains={'source_type': 'soil_water_content'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 6. All other parameters are used. Response has 2 subscriptions.
# The response is unrealistic here, but we are just testing the query parameter handling.
api_mock.route(
    M(url=TEST_URL),
    M(
        params__contains={
            'name': 'test xyz',
            'name__contains': 'xyz',
            'created': '2018-02-12T00:00:00Z/..',
            'updated': '../2018-03-18T12:31:12Z',
            'start_time': '2018-01-01T00:00:00Z',
            'end_time': '2022-01-01T00:00:00Z/2024-01-01T00:00:00Z',
            'hosting': 'true',
            'sort_by': 'name DESC',
        })).mock(side_effect=[
            Response(200, json={'subscriptions': [{
                'id': 1
            }, {
                'id': 2
            }]})
        ])

# 7. No status or source_type requested. Response is the same as for 1.
api_mock.route(M(url=TEST_URL)).mock(side_effect=[
    Response(200, json=page) for page in subscription_pages(size=40)
])


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


@pytest.mark.anyio
@failing_api_mock
async def test_list_subscriptions_failure():
    """ServerError is raised if there is an internal server error (500)."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [sub async for sub in client.list_subscriptions()]


@pytest.mark.parametrize("status, count", [({"running"}, 100), ({"failed"}, 0),
                                           (None, 100)])
@pytest.mark.anyio
@api_mock
async def test_list_subscriptions_success(
    status,
    count,
):
    """Account subscriptions iterator yields expected descriptions."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        assert len([
            sub async for sub in client.list_subscriptions(status=status)
        ]) == count


@pytest.mark.parametrize("source_type, count",
                         [("catalog", 100), ("soil_water_content", 0),
                          (None, 100)])
@pytest.mark.anyio
@api_mock
async def test_list_subscriptions_source_type_success(
    source_type,
    count,
):
    """Account subscriptions iterator yields expected descriptions."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        assert len([
            sub
            async for sub in client.list_subscriptions(source_type=source_type)
        ]) == count


@pytest.mark.anyio
@api_mock
async def test_list_subscriptions_filtering_and_sorting():
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        assert len([
            sub async for sub in client.list_subscriptions(
                name='test xyz', name__contains='xyz',
                created='2018-02-12T00:00:00Z/..',
                updated='../2018-03-18T12:31:12Z',
                start_time='2018-01-01T00:00:00Z',
                end_time='2022-01-01T00:00:00Z/2024-01-01T00:00:00Z',
                hosting=True, sort_by='name DESC')
        ]) == 2


@pytest.mark.anyio
@failing_api_mock
async def test_create_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.create_subscription({"lol": "wut"})


@pytest.mark.anyio
@create_mock
async def test_create_subscription_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.create_subscription({
            'name': 'test', 'delivery': 'yes, please', 'source': 'test'
        })
        assert sub['name'] == 'test'


@pytest.mark.anyio
@create_mock
async def test_create_subscription_with_hosting_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.create_subscription({
            'name': 'test', 'source': 'test', 'hosting': 'yes, please'
        })
        assert sub['name'] == 'test'


@pytest.mark.anyio
@failing_api_mock
async def test_cancel_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.cancel_subscription("lolwut")


@pytest.mark.anyio
@cancel_mock
async def test_cancel_subscription_success():
    """Subscription is canceled, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        _ = await client.cancel_subscription("test")


@pytest.mark.anyio
@failing_api_mock
async def test_update_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.update_subscription("lolwut", {})


@pytest.mark.anyio
@update_mock
async def test_update_subscription_success():
    """Subscription is updated, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.update_subscription(
            "test", {
                "name": "test", "delivery": "no, thanks", "source": "test"
            })
        assert sub["delivery"] == "no, thanks"


@pytest.mark.anyio
@patch_mock
async def test_patch_subscription_success():
    """Subscription is patched, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.patch_subscription("test", {"name": "test patch"})
        assert sub["name"] == "test patch"


@pytest.mark.anyio
@failing_api_mock
async def test_get_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.get_subscription("lolwut")


@pytest.mark.anyio
@get_mock
async def test_get_subscription_success(monkeypatch):
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.get_subscription("test")
        assert sub['delivery'] == "yes, please"


@pytest.mark.anyio
@failing_api_mock
async def test_get_results_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [res async for res in client.get_results("lolwut")]


@pytest.mark.anyio
@res_api_mock
async def test_get_results_success():
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        results = [res async for res in client.get_results("42")]
        assert len(results) == 100


@pytest.mark.anyio
@res_api_mock
async def test_get_results_csv():
    """Subscription CSV fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        results = [res async for res in client.get_results_csv("42")]
        rows = list(csv.reader(results))
        assert rows == [['id', 'status'], ['1234-abcd', 'SUCCESS']]


paging_cycle_api_mock = respx.mock()

# Identical next links is a hangup we want to avoid.
paging_cycle_api_mock.route(M(url__startswith=TEST_URL)).mock(side_effect=[
    Response(200,
             json={
                 'subscriptions': [{
                     'id': '1'
                 }], '_links': {
                     "next": TEST_URL
                 }
             }),
    Response(200,
             json={
                 'subscriptions': [{
                     'id': '2'
                 }], '_links': {
                     "next": TEST_URL
                 }
             })
])


@pytest.mark.anyio
@paging_cycle_api_mock
async def test_list_subscriptions_cycle_break():
    """PagingError is raised if there is a paging cycle."""
    with pytest.raises(PagingError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [sub async for sub in client.list_subscriptions()]
