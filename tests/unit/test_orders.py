"""Tests of Orders client and aiohttp implementation."""

import itertools
import uuid
from unittest.mock import Mock, patch

import pytest

from planet.clients.orders import Order, OrdersClient, OrderError


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.post")
async def test_create_order_failure(mock_http_post):
    """Get expected chained exception on fake service failure."""

    # create_order() interacts with the Planet Orders service only via
    # HTTP POST request. Here we patch the post() method of the aiohttp
    # ClientSession class and program the mock object to raise an
    # exception when its raise_for_status() method is called. Note that
    # raise_for_status() is a normal (not-async) Python method and so
    # we must explicitly use (not-async) Mock. Otherwise all the
    # attributes of mock_http_post will be AsyncMock objects.
    mock_http_post.return_value.__aenter__.return_value.raise_for_status = Mock(
        side_effect=RuntimeError("Boom! Service failure"))

    # In this demo version of OrdersClient a session is created
    # internally and so we don't need to give it one.
    client = OrdersClient(None)
    with pytest.raises(OrderError) as excinfo:
        await client.create_order({})

    assert type(excinfo.value.__context__) == RuntimeError
    assert str(excinfo.value.__context__) == "Boom! Service failure"


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.post")
async def test_create_order_success(mock_http_post):
    """Submit a fake order to fake service and get expected response."""

    # In this test we want the response to the POST request to not raise
    # an exception.
    mock_http_post.return_value.__aenter__.return_value.raise_for_status = Mock(
        return_value=None)

    # create_order() async enters the response to an HTTP POST request
    # and awaits the response's json() method. We program the return
    # value of that method with an abbreviated Orders service response.
    mock_http_post.return_value.__aenter__.return_value.json.return_value = {
        "id": "lolwut",
        "state": "queued"
    }

    client = OrdersClient(None)

    # We provide an abbreviated fake orders request. create_orders()
    # does not validate requests.
    order = await client.create_order({"name": "fake order"})

    # Note that create_orders() does not validate service responses.
    assert order.id == "lolwut"
    assert order.state == "queued"


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.get")
async def test_wait_service_failure(mock_http_get):
    """Get expected chained exception on fake service failure."""
    mock_http_get.return_value.__aenter__.return_value.raise_for_status = Mock(
        side_effect=RuntimeError("Boom! Service failure"))

    # Order description endpoint URL construction requires a UUID id.
    order = Order({"id": str(uuid.uuid4()), "state": "queued"})

    client = OrdersClient(None)
    with pytest.raises(OrderError) as excinfo:
        await client.wait(order)

    assert type(excinfo.value.__context__) == RuntimeError
    assert str(excinfo.value.__context__) == "Boom! Service failure"


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.get")
@patch("planet.clients.orders.POLL_SLEEP", 0.01)
async def test_wait_timeout(mock_http_get):
    """Get OrderError when max polling requests has been reached."""
    # We script the service responses to always succeed, return "queued"
    # the first time, and "running" infinitely thereafter.
    mock_http_get.return_value.__aenter__.return_value.raise_for_status = Mock(
        return_value=None)
    mock_http_get.return_value.__aenter__.return_value.json.side_effect = itertools.chain(
        [{
            "state": "queued"
        }], itertools.repeat({"state": "running"}))

    # Order description endpoint URL construction requires a UUID id.
    order = Order({"id": str(uuid.uuid4()), "state": "queued"})

    client = OrdersClient(None)
    with pytest.raises(OrderError):
        await client.wait(order, max_requests=3)

    assert mock_http_get.call_count == 3


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.get")
@patch("planet.clients.orders.POLL_SLEEP", 0.01)
async def test_wait_success(mock_http_get):
    """Wait and return final state."""
    # We script the service responses to always succeed, return
    # "running" the first few times, and "success" infinitely
    # thereafter.
    mock_http_get.return_value.__aenter__.return_value.raise_for_status = Mock(
        return_value=None)
    mock_http_get.return_value.__aenter__.return_value.json.side_effect = itertools.chain(
        itertools.repeat({"state": "queued"}, 3),
        itertools.repeat({"state": "success"}))

    # Order description endpoint URL construction requires a UUID id.
    order = Order({"id": str(uuid.uuid4()), "state": "queued"})

    client = OrdersClient(None)
    assert "success" == await client.wait(order)
