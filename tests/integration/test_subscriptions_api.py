"""Tests of the Planet Subscriptions API client."""

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

# Mock router representing an API that returns only a 500
# internal server error. The router is configured outside the test
# to help keep our test more readable.
failing_api_mock = respx.mock()
failing_api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1')).mock(
        return_value=Response(500, json={
            "code": 0, "message": "string"
        }))


def result_pages(status=None, size=40):
    """Helper for creating fake subscriptions listing pages."""
    all_subs = [{'id': str(i), 'status': 'created'} for i in range(1, 101)]
    select_subs = (sub for sub in all_subs
                   if not status or sub['status'] in status)
    pages = []
    for group in zip_longest(*[iter(select_subs)] * size):
        subs = list(sub for sub in group if sub is not None)
        page = {'subscriptions': subs, '_links': {}}
        pm = datetime.now().isoformat()
        if len(subs) == size:
            page['_links'][
                'next'] = f'https://api.planet.com/subscriptions/v1?pm={pm}'
        pages.append(page)
    return pages


# By default, respx's mock router asserts that all configured routes
# are followed in a test. Each of our parameterized tests follows only
# one route, so if we want to configure routes once and reuse them, we
# must disable the default.
api_mock = respx.mock(assert_all_called=False)

# 1. Request for status: created. Response has three pages.
api_mock.route(M(url__startswith='https://api.planet.com/subscriptions/v1'),
               M(params__contains={'status': 'created'})).mock(side_effect=[
                   Response(200, json=page)
                   for page in result_pages(status={'created'}, size=40)
               ])

# 2. Request for status: failed. Response has a single empty page.
api_mock.route(M(url__startswith='https://api.planet.com/subscriptions/v1'),
               M(params__contains={'status': 'failed'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 3. Request for status: queued. Response has a single empty page.
api_mock.route(M(url__startswith='https://api.planet.com/subscriptions/v1'),
               M(params__contains={'status': 'queued'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])

# 4. No status requested. Response is the same as for 1.
api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1')
).mock(
    side_effect=[Response(200, json=page) for page in result_pages(size=40)])


# The "creation", "update", and "cancel" mock APIs return submitted
# data to the caller. They are used to test methods that rely on POST
# or PUT.
def modify_response(request):
    if request.content:
        return Response(200, json=json.loads(request.content))
    else:
        return Response(200)


create_mock = respx.mock()
create_mock.route(host='api.planet.com',
                  path='/subscriptions/v1',
                  method='POST').mock(side_effect=modify_response)

update_mock = respx.mock()
update_mock.route(host='api.planet.com',
                  path__regex=r'^/subscriptions/v1/(\w+)',
                  method='PUT').mock(side_effect=modify_response)

cancel_mock = respx.mock()
cancel_mock.route(host='api.planet.com',
                  path__regex=r'^/subscriptions/v1/(\w+)/cancel',
                  method='POST').mock(side_effect=modify_response)

# Mock the subscription description API endpoint.
describe_mock = respx.mock()
describe_mock.route(
    host='api.planet.com',
    path__regex=r'^/subscriptions/v1/(\w+)',
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
            url = f'https://api.planet.com/subscriptions/v1/42/results?pm={pm}'
            page['_links']['next'] = url
        pages.append(page)
    return pages


# By default, respx's mock router asserts that all configured routes
# are followed in a test. Each of our parameterized tests follows only
# one route, so if we want to configure routes once and reuse them, we
# must disable the default.
res_api_mock = respx.mock(assert_all_called=False)

# 1. Request for status: created. Response has three pages.
res_api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1'),
    M(params__contains={'status': 'created'})).mock(side_effect=[
        Response(200, json=page)
        for page in result_pages(status={'created'}, size=40)
    ])

# 2. Request for status: queued. Response has a single empty page.
res_api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1'),
    M(params__contains={'status': 'queued'})).mock(
        side_effect=[Response(200, json={'results': []})])

# 3. No status requested. Response is the same as for 1.
res_api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1')
).mock(
    side_effect=[Response(200, json=page) for page in result_pages(size=40)])


@pytest.mark.asyncio
@failing_api_mock
async def test_list_subscriptions_failure():
    """ServerError is raised if there is an internal server error (500)."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = [sub async for sub in client.list_subscriptions()]


@pytest.mark.parametrize("status, count", [({"created"}, 100), ({"failed"}, 0),
                                           (None, 100)])
@pytest.mark.asyncio
@api_mock
async def test_list_subscriptions_success(
    status,
    count,
):
    """Account subscriptions iterator yields expected descriptions."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        assert len([
            sub async for sub in client.list_subscriptions(status=status)
        ]) == count


@pytest.mark.asyncio
@failing_api_mock
async def test_create_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.create_subscription({"lol": "wut"})


@pytest.mark.asyncio
@create_mock
async def test_create_subscription_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.create_subscription({
            'name': 'test', 'delivery': 'yes, please', 'source': 'test'
        })
        assert sub['name'] == 'test'


@pytest.mark.asyncio
@failing_api_mock
async def test_cancel_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.cancel_subscription("lolwut")


@pytest.mark.asyncio
@cancel_mock
async def test_cancel_subscription_success():
    """Subscription is canceled, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        _ = await client.cancel_subscription("test")


@pytest.mark.asyncio
@failing_api_mock
async def test_update_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.update_subscription("lolwut", {})


@pytest.mark.asyncio
@update_mock
async def test_update_subscription_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.update_subscription(
            "test", {
                'name': 'test', 'delivery': "no, thanks", 'source': 'test'
            })
        assert sub['delivery'] == "no, thanks"


@pytest.mark.asyncio
@failing_api_mock
async def test_get_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.get_subscription("lolwut")


@pytest.mark.asyncio
@describe_mock
async def test_get_subscription_success(monkeypatch):
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.get_subscription("test")
        assert sub['delivery'] == "yes, please"


@pytest.mark.asyncio
@failing_api_mock
async def test_get_results_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = [res async for res in client.get_results("lolwut")]


@pytest.mark.asyncio
@res_api_mock
async def test_get_results_success():
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        results = [res async for res in client.get_results("42")]
        assert len(results) == 100


paging_cycle_api_mock = respx.mock()

# Identical next links is a hangup we want to avoid.
paging_cycle_api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1')).mock(
        side_effect=[
            Response(200,
                     json={
                         'subscriptions': [{
                             'id': '1'
                         }],
                         '_links': {
                             "next": 'https://api.planet.com/subscriptions/v1'
                         }
                     }),
            Response(200,
                     json={
                         'subscriptions': [{
                             'id': '2'
                         }],
                         '_links': {
                             "next": 'https://api.planet.com/subscriptions/v1'
                         }
                     })
        ])


@pytest.mark.asyncio
@paging_cycle_api_mock
async def test_list_subscriptions_cycle_break():
    """PagingError is raised if there is a paging cycle."""
    with pytest.raises(PagingError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = [sub async for sub in client.list_subscriptions()]
