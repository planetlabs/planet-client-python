"""Tests of the Planet Subscriptions API client."""

import pytest

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


@pytest.mark.xfail(reason="Client/server interaction not yet implemented")
@pytest.mark.parametrize("status, count", [({"created"}, 100), ({"failed"}, 0),
                                           (None, 100)])
@pytest.mark.asyncio
async def test_list_subscriptions_success(status, count, monkeypatch):
    """Account subscriptions iterator yields expected descriptions."""
    monkeypatch.setattr(planet.clients.subscriptions,
                        '_fake_subs',
                        {str(i): {
                            'status': 'created'
                        }
                         for i in range(101)})
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
