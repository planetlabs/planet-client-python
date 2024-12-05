"""Tests of the Planet Subscriptions API client."""

import csv

import pytest

from planet.clients.subscriptions import SubscriptionsClient
from planet.exceptions import APIError, PagingError, ServerError
from planet.http import Session
from planet.test import TEST_URL, MockSubscriptionsAPI

mock_subscriptions_api = MockSubscriptionsAPI()

@pytest.mark.anyio
@mock_subscriptions_api.failure
async def test_list_subscriptions_failure():
    """ServerError is raised if there is an internal server error (500)."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [sub async for sub in client.list_subscriptions()]


@pytest.mark.parametrize("status, count", [({"running"}, 100), ({"failed"}, 0),
                                           (None, 100)])
@pytest.mark.anyio
@mock_subscriptions_api.success
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
@mock_subscriptions_api.success
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
@mock_subscriptions_api.failure
async def test_create_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.create_subscription({"lol": "wut"})


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_create_subscription_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.create_subscription({
            'name': 'test', 'delivery': 'yes, please', 'source': 'test'
        })
        assert sub['name'] == 'test'


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_create_subscription_with_hosting_success():
    """Subscription is created, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.create_subscription({
            'name': 'test', 'source': 'test', 'hosting': 'yes, please'
        })
        assert sub['name'] == 'test'


@pytest.mark.anyio
@mock_subscriptions_api.failure
async def test_cancel_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.cancel_subscription("lolwut")


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_cancel_subscription_success():
    """Subscription is canceled, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        _ = await client.cancel_subscription("test")


@pytest.mark.anyio
@mock_subscriptions_api.failure
async def test_update_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.update_subscription("lolwut", {})


@pytest.mark.anyio
@mock_subscriptions_api.success
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
@mock_subscriptions_api.success
async def test_patch_subscription_success():
    """Subscription is patched, description has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.patch_subscription("test", {"name": "test patch"})
        assert sub["name"] == "test patch"


@pytest.mark.anyio
@mock_subscriptions_api.failure
async def test_get_subscription_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(ServerError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = await client.get_subscription("lolwut")


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_get_subscription_success(monkeypatch):
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        sub = await client.get_subscription("test")
        assert sub['delivery'] == "yes, please"


@pytest.mark.anyio
@mock_subscriptions_api.failure
async def test_get_results_failure():
    """APIError is raised if there is a server error."""
    with pytest.raises(APIError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [res async for res in client.get_results("lolwut")]


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_get_results_success():
    """Subscription description fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        results = [res async for res in client.get_results("42")]
        assert len(results) == 100


@pytest.mark.anyio
@mock_subscriptions_api.success
async def test_get_results_csv():
    """Subscription CSV fetched, has the expected items."""
    async with Session() as session:
        client = SubscriptionsClient(session, base_url=TEST_URL)
        results = [res async for res in client.get_results_csv("42")]
        rows = list(csv.reader(results))
        assert rows == [['id', 'status'], ['1234-abcd', 'SUCCESS']]


@pytest.mark.anyio
@mock_subscriptions_api.paging_cycle
async def test_list_subscriptions_cycle_break():
    """PagingError is raised if there is a paging cycle."""
    with pytest.raises(PagingError):
        async with Session() as session:
            client = SubscriptionsClient(session, base_url=TEST_URL)
            _ = [sub async for sub in client.list_subscriptions()]
