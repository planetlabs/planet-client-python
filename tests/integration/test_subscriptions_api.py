"""Tests of the Planet Subscriptions API client."""

from datetime import datetime
from itertools import zip_longest
from turtle import pd
from unittest.mock import ANY

from httpx import Response
import pytest
import respx
from respx.patterns import M

import planet.clients.subscriptions
from planet.clients.subscriptions import SubscriptionsClient
from planet.exceptions import APIError
from planet.http import Session


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_list_subscriptions_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", 0)
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = [sub async for sub in client.list_subscriptions()]


# Mock the responses of a server which has 100 subscriptions in the
# 'created' state and serves them in pages of 40.
all_subs = [{'id': str(i), 'status': 'created'} for i in range(1, 101)]


def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == 'fill':
        return zip_longest(*args, fillvalue=fillvalue)
    if incomplete == 'strict':
        return zip(*args, strict=True)
    if incomplete == 'ignore':
        return zip(*args)
    else:
        raise ValueError('Expected fill, strict, or ignore')


def sub_pages(status=None, size=40):
    select_subs = (sub for sub in all_subs
                   if not status or sub['status'] in status)
    pages = []
    for group in grouper(select_subs, size):
        subs = list(sub for sub in group if sub is not None)
        page = {'subscriptions': subs, '_links': {}}
        if len(subs) == size:
            page['_links'][
                'next'] = f'https://api.planet.com/subscriptions/v1?page_marker={datetime.now().isoformat()}'
        pages.append(page)
    return pages


api_mock = respx.mock(assert_all_called=False)

api_mock.route(M(url__startswith='https://api.planet.com/subscriptions/v1'),
               M(params__contains={'status': 'created'})).mock(side_effect=[
                   Response(200, json=page)
                   for page in sub_pages(status={'created'}, size=40)
               ])
# 2. Request for status: anything but created. Response has a single page.
api_mock.route(M(url__startswith='https://api.planet.com/subscriptions/v1'),
               M(params__contains={'status': 'failed'})).mock(
                   side_effect=[Response(200, json={'subscriptions': []})])
# 3. No status requested. Response is the same as for 1.
api_mock.route(
    M(url__startswith='https://api.planet.com/subscriptions/v1')).mock(
        side_effect=[Response(200, json=page) for page in sub_pages(size=40)])


@pytest.mark.parametrize("status, count", [({"created"}, 100), ({"failed"}, 0),
                                           (None, 100)])
@pytest.mark.asyncio
@api_mock
async def test_list_subscriptions_success(status, count, monkeypatch):
    """Account subscriptions iterator yields expected descriptions."""
    async with Session() as session:
        client = SubscriptionsClient(session)
        assert len([
            sub async for sub in client.list_subscriptions(status=status)
        ]) == count


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_create_subscription_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", {})
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.create_subscription({"lol": "wut"})


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_create_subscription_success(monkeypatch):
    """Subscription is created, description has the expected items."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", {})
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.create_subscription({
            'name': 'test', 'delivery': 'yes, please', 'source': 'test'
        })
        assert sub['name'] == 'test'


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_cancel_subscription_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", {})
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.cancel_subscription("lolwut")


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_cancel_subscription_success(monkeypatch):
    """Subscription is canceled, description has the expected items."""
    monkeypatch.setattr(
        planet.clients.subscriptions,
        "_fake_subs", {
            "test": {
                'name': 'test', 'delivery': 'yes, please', 'source': 'test'
            }
        })
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.cancel_subscription("test")
        assert sub['name'] == 'test'


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_update_subscription_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", {})
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.update_subscription("lolwut", {})


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_update_subscription_success(monkeypatch):
    """Subscription is created, description has the expected items."""
    monkeypatch.setattr(
        planet.clients.subscriptions,
        "_fake_subs", {
            "test": {
                'name': 'test', 'delivery': 'yes, please', 'source': 'test'
            }
        })
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.update_subscription(
            "test", {
                'name': 'test', 'delivery': "no, thanks", 'source': 'test'
            })
        assert sub['delivery'] == "no, thanks"


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_get_subscription_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_subs", {})
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = await client.get_subscription("lolwut")


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_get_subscription_success(monkeypatch):
    """Subscription description fetched, has the expected items."""
    monkeypatch.setattr(
        planet.clients.subscriptions,
        "_fake_subs", {
            "test": {
                'name': 'test', 'delivery': 'yes, please', 'source': 'test'
            }
        })
    async with Session() as session:
        client = SubscriptionsClient(session)
        sub = await client.get_subscription("test")
        assert sub['delivery'] == "yes, please"


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_get_results_failure(monkeypatch):
    """APIError is raised if there is a server error."""
    monkeypatch.setattr(planet.clients.subscriptions, "_fake_sub_results", {})
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session)
            _ = [res async for res in client.get_results("lolwut")]


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.asyncio
async def test_get_results_success(monkeypatch):
    """Subscription description fetched, has the expected items."""
    monkeypatch.setattr(
        planet.clients.subscriptions,
        '_fake_sub_results',
        {'42': [{
            'id': f'r{i}', 'status': 'created'
        } for i in range(101)]})
    async with Session() as session:
        client = SubscriptionsClient(session)
        results = [res async for res in client.get_results("42")]
        assert len(results) == 100
