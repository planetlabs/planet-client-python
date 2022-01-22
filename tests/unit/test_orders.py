"""Tests of Orders client."""

from unittest.mock import patch

import pytest

import planet.clients.orders
from planet.clients.orders import OrdersClient
from planet.order_request import build_request, product


@pytest.mark.asyncio
@patch("planet.clients.orders.ClientSession.post")
async def test_create_order(mock_post, event_loop):
    """Create an order."""
    image_ids = ['3949357_1454705_2020-12-01_241c']
    request = build_request('test_order',
                            [product(image_ids, 'analytic', 'psorthotile')])

    mock_post.return_value.__aenter__.return_value.json.return_value = {
        "id": "lol",
        "state": "wut"
    }

    async def coro():
        client = OrdersClient(None)
        return await client.create_order(request)

    order = await event_loop.create_task(coro())
    assert order.id == "lol"
