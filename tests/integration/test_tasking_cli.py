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
"""Test Tasking CLI"""

import json
from http import HTTPStatus

from click.testing import CliRunner
import httpx
import pytest
import respx

from planet.cli import cli

TEST_URL = 'https://api.planet.com/tasking/v2'
TEST_ORDERS_URL = f'{TEST_URL}/orders'


@pytest.fixture
def invoke():
    """Helper to invoke CLI commands."""

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = ['tasking'] + extra_args
        return runner.invoke(cli.main, args=args)

    return _invoke


@pytest.fixture
def tasking_order_json():
    """Sample tasking order JSON."""
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
        'last_modified': '2023-01-01T00:00:00Z'
    }


@pytest.fixture
def tasking_orders_list_json():
    """Sample tasking orders list JSON."""
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


@respx.mock
def test_create_order_with_name_and_geometry(invoke, tasking_order_json):
    """Test creating a tasking order with name and geometry."""
    mock_resp = httpx.Response(HTTPStatus.CREATED, json=tasking_order_json)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke([
        'create-order',
        '--name',
        'test_order',
        '--geometry',
        '{"type":"Point","coordinates":[-122,37]}'
    ])

    assert result.exit_code == 0
    assert 'test_tasking_order' in result.output


@respx.mock
def test_create_order_with_request_file(invoke, tasking_order_json, tmp_path):
    """Test creating a tasking order with request file."""
    request_data = {
        'name': 'test_tasking_order',
        'geometry': {
            'type': 'Point', 'coordinates': [-122.0, 37.0]
        },
        'products': [{
            'item_type': 'skysat_collect', 'asset_type': 'ortho_analytic'
        }]
    }

    request_file = tmp_path / 'request.json'
    request_file.write_text(json.dumps(request_data))

    mock_resp = httpx.Response(HTTPStatus.CREATED, json=tasking_order_json)
    respx.post(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['create-order', '--request', str(request_file)])

    assert result.exit_code == 0
    assert 'test_tasking_order' in result.output


def test_create_order_missing_args(invoke):
    """Test creating a tasking order with missing arguments."""
    result = invoke(['create-order'])

    assert result.exit_code != 0
    assert 'Either --request file or --name and --geometry must be provided' in result.output


@respx.mock
def test_get_order(invoke, tasking_order_json):
    """Test getting a tasking order."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    get_url = f'{TEST_ORDERS_URL}/{order_id}'

    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_order_json)
    respx.get(get_url).return_value = mock_resp

    result = invoke(['get-order', order_id])

    assert result.exit_code == 0
    assert order_id in result.output
    assert 'test_tasking_order' in result.output


@respx.mock
def test_cancel_order(invoke, tasking_order_json):
    """Test cancelling a tasking order."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    cancel_url = f'{TEST_ORDERS_URL}/{order_id}'

    cancelled_order = tasking_order_json.copy()
    cancelled_order['state'] = 'cancelled'

    mock_resp = httpx.Response(HTTPStatus.OK, json=cancelled_order)
    respx.patch(cancel_url).return_value = mock_resp

    result = invoke(['cancel-order', order_id])

    assert result.exit_code == 0
    assert 'cancelled' in result.output


@respx.mock
def test_list_orders(invoke, tasking_orders_list_json):
    """Test listing tasking orders."""
    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_orders_list_json)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list-orders'])

    assert result.exit_code == 0
    assert '550e8400-e29b-41d4-a716-446655440000' in result.output
    assert '550e8400-e29b-41d4-a716-446655440001' in result.output


@respx.mock
def test_list_orders_with_state_filter(invoke, tasking_orders_list_json):
    """Test listing tasking orders with state filter."""
    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_orders_list_json)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list-orders', '--state', 'success'])

    assert result.exit_code == 0


@respx.mock
def test_list_orders_with_limit(invoke, tasking_orders_list_json):
    """Test listing tasking orders with limit."""
    mock_resp = httpx.Response(HTTPStatus.OK, json=tasking_orders_list_json)
    respx.get(TEST_ORDERS_URL).return_value = mock_resp

    result = invoke(['list-orders', '--limit', '1'])

    assert result.exit_code == 0


@respx.mock
def test_wait_order(invoke, tasking_order_json):
    """Test waiting for a tasking order."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    get_url = f'{TEST_ORDERS_URL}/{order_id}'

    # Return success state immediately
    success_order = tasking_order_json.copy()
    success_order['state'] = 'success'

    mock_resp = httpx.Response(HTTPStatus.OK, json=success_order)
    respx.get(get_url).return_value = mock_resp

    result = invoke(
        ['wait-order', order_id, '--delay', '0.1', '--max-attempts', '1'])

    assert result.exit_code == 0
    assert 'success' in result.output


@respx.mock
def test_wait_order_with_custom_state(invoke, tasking_order_json):
    """Test waiting for a tasking order with custom state."""
    order_id = '550e8400-e29b-41d4-a716-446655440000'
    get_url = f'{TEST_ORDERS_URL}/{order_id}'

    # Return running state
    running_order = tasking_order_json.copy()
    running_order['state'] = 'running'

    mock_resp = httpx.Response(HTTPStatus.OK, json=running_order)
    respx.get(get_url).return_value = mock_resp

    result = invoke([
        'wait-order',
        order_id,
        '--state',
        'running',
        '--delay',
        '0.1',
        '--max-attempts',
        '1'
    ])

    assert result.exit_code == 0
    assert 'running' in result.output


@respx.mock
def test_get_results(invoke):
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

    result = invoke(['get-results', order_id])

    assert result.exit_code == 0
    assert 'ortho_analytic' in result.output
    assert 'ortho_visual' in result.output


def test_tasking_help(invoke):
    """Test tasking command help."""
    result = invoke(['--help'])

    assert result.exit_code == 0
    assert 'tasking' in result.output


def test_create_order_help(invoke):
    """Test create-order command help."""
    result = invoke(['create-order', '--help'])

    assert result.exit_code == 0
    assert 'Create a tasking order' in result.output
