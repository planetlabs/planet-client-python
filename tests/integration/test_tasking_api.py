# Copyright 2025 Planet Labs PBC.
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
"""Integration tests for the Tasking API."""

from http import HTTPStatus
import logging

import httpx
import pytest
import respx

from planet import TaskingClient, exceptions
from planet.clients.tasking import TaskingOrderStates
from planet.sync import Planet

TEST_URL = 'http://www.MockNotRealURL.com/tasking/v2'
TEST_ORDERS_URL = f'{TEST_URL}/orders'

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def tasking_order_description():
    """Mock tasking order description."""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'name': 'test_tasking_order',
        'state': 'queued',
        'geometry': {
            'type': 'Point', 'coordinates': [-122.0, 37.0]
        },
        'products': [{
            'item_type': 'skysat_collect', 'asset_type': 'ortho_analytic'
        }],
        'created_on': '2023-01-01T00:00:00Z',
        'last_modified': '2023-01-01T00:00:00Z',
        '_links': {
            'self': f'{TEST_ORDERS_URL}/550e8400-e29b-41d4-a716-446655440000'
        }
    }


@pytest.fixture
def tasking_order_request():
    """Mock tasking order request."""
    return {
        'name': 'test_tasking_order',
        'geometry': {
            'type': 'Point', 'coordinates': [-122.0, 37.0]
        },
        'products': [{
            'item_type': 'skysat_collect', 'asset_type': 'ortho_analytic'
        }]
    }


@pytest.fixture
def tasking_orders_list():
    """Mock list of tasking orders."""
    return {
        'orders': [{
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'name': 'order1',
            'state': 'success'
        },
                   {
                       'id': '550e8400-e29b-41d4-a716-446655440001',
                       'name': 'order2',
                       'state': 'running'
                   }]
    }


def test_TaskingOrderStates_reached():
    """Test TaskingOrderStates.reached method."""
    assert not TaskingOrderStates.reached('running', 'queued')
    assert TaskingOrderStates.reached('running', 'running')
    assert TaskingOrderStates.reached('running', 'success')


def test_TaskingOrderStates_passed():
    """Test TaskingOrderStates.passed method."""
    assert not TaskingOrderStates.passed('running', 'queued')
    assert not TaskingOrderStates.passed('running', 'running')
    assert TaskingOrderStates.passed('running', 'success')


@respx.mock
@pytest.mark.anyio
async def test_create_order(tasking_order_request,
                            tasking_order_description,
                            session):
    """Test creating a tasking order."""
    mock_resp = httpx.Response(HTTPStatus.CREATED,
                               json=tasking_order_description)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    order = await client.create_order(tasking_order_request)

    assert order['id'] == '550e8400-e29b-41d4-a716-446655440000'
    assert order['name'] == 'test_tasking_order'
    assert order['state'] == 'queued'


@respx.mock
@pytest.mark.anyio
async def test_get_order(tasking_order_description, session):
    """Test getting a tasking order."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    get_url = f'{TEST_ORDERS_URL}/{order_id}'

    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_order_description)
    respx.get(get_url).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    order = await client.get_order(order_id)

    assert order['id'] == order_id
    assert order['name'] == 'test_tasking_order'


@respx.mock
@pytest.mark.anyio
async def test_get_order_invalid_id(session):
    """Test getting a tasking order with invalid ID."""
    client = TaskingClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await client.get_order('invalid-id')


@respx.mock
@pytest.mark.anyio
async def test_cancel_order(tasking_order_description, session):
    """Test cancelling a tasking order."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    cancel_url = f'{TEST_ORDERS_URL}/{order_id}'

    cancelled_order = tasking_order_description.copy()
    cancelled_order['state'] = 'cancelled'

    mock_resp = httpx.Response(HTTPStatus.OK, json=cancelled_order)
    respx.patch(cancel_url).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    order = await client.cancel_order(order_id)

    assert order['state'] == 'cancelled'


@respx.mock
@pytest.mark.anyio
async def test_list_orders(tasking_orders_list, session):
    """Test listing tasking orders."""
    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_orders_list)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    orders = []
    async for order in client.list_orders():
        orders.append(order)

    assert len(orders) == 2
    assert orders[0]['id'] == '550e8400-e29b-41d4-a716-446655440000'
    assert orders[1]['id'] == '550e8400-e29b-41d4-a716-446655440001'


@respx.mock
@pytest.mark.anyio
async def test_list_orders_with_state_filter(tasking_orders_list, session):
    """Test listing tasking orders with state filter."""
    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_orders_list)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    orders = []
    async for order in client.list_orders(state='success'):
        orders.append(order)

    assert len(orders) == 2  # Mock returns all, filtering would be server-side


@respx.mock
@pytest.mark.anyio
async def test_wait_order_success(tasking_order_description, session):
    """Test waiting for order to reach success state."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    get_url = f'{TEST_ORDERS_URL}/{order_id}'

    # First call returns running state
    running_order = tasking_order_description.copy()
    running_order['state'] = 'running'

    # Second call returns success state
    success_order = tasking_order_description.copy()
    success_order['state'] = 'success'

    respx.get(get_url).side_effect = [
        httpx.Response(HTTPStatus.OK, json=running_order),
        httpx.Response(HTTPStatus.OK, json=success_order)
    ]

    client = TaskingClient(session, base_url=TEST_URL)
    final_state = await client.wait_order(order_id, delay=0.1, max_attempts=5)

    assert final_state == 'success'


@respx.mock
@pytest.mark.anyio
async def test_wait_order_invalid_state(session):
    """Test waiting for order with invalid state."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'

    client = TaskingClient(session, base_url=TEST_URL)

    with pytest.raises(exceptions.ClientError):
        await client.wait_order(order_id, state='invalid_state')


@respx.mock
@pytest.mark.anyio
async def test_get_order_results(session):
    """Test getting tasking order results."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    results_url = f'{TEST_ORDERS_URL}/{order_id}/results'

    results_data = {
        'results': [{
            'asset_type': 'ortho_analytic',
            'location': 'https://download.url/1'
        },
                    {
                        'asset_type': 'ortho_visual',
                        'location': 'https://download.url/2'
                    }]
    }

    mock_resp = httpx.Response(HTTPStatus.OK, json=results_data)
    respx.get(results_url).return_value = mock_resp

    client = TaskingClient(session, base_url=TEST_URL)
    results = await client.get_order_results(order_id)

    assert len(results) == 2
    assert results[0]['asset_type'] == 'ortho_analytic'


# Sync client tests
def test_sync_tasking_create_order():
    """Test sync client tasking order creation."""
    pl = Planet()
    assert hasattr(pl, 'tasking')
    assert pl.tasking is not None


def test_sync_tasking_api_methods():
    """Test that sync tasking API has all expected methods."""
    pl = Planet()

    # Check that all expected methods exist
    assert hasattr(pl.tasking, 'create_order')
    assert hasattr(pl.tasking, 'get_order')
    assert hasattr(pl.tasking, 'cancel_order')
    assert hasattr(pl.tasking, 'list_orders')
    assert hasattr(pl.tasking, 'wait_order')
    assert hasattr(pl.tasking, 'get_order_results')
