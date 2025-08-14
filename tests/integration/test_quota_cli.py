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
from http import HTTPStatus
import json
import tempfile
import httpx
import pytest
import respx
from click.testing import CliRunner
from planet.cli.quota import quota

pytestmark = pytest.mark.anyio
# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.planet.com/quota/v1"
TEST_RESERVATION_REQUEST = {
    "name": "Test Reservation",
    "products": ["PSScene"],
    "item_types": ["PSScene4Band"],
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[-122.5, 37.7], [-122.4, 37.7], [-122.4, 37.8],
                         [-122.5, 37.8], [-122.5, 37.7]]]
    }
}
TEST_RESERVATION_RESPONSE = {
    "id": "12345678-1234-5678-9012-123456789012",
    "name": "Test Reservation",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z"
}
TEST_RESERVATIONS_LIST = {
    "reservations": [TEST_RESERVATION_RESPONSE], "_next": None
}
TEST_ESTIMATE_RESPONSE = {
    "estimated_cost": 100.0,
    "estimated_usage": {
        "area_km2": 25.0, "item_count": 10
    }
}
TEST_QUOTA_USAGE = {
    "current_usage": {
        "area_km2": 150.0, "item_count": 50
    },
    "quota_limits": {
        "area_km2": 1000.0, "item_count": 500
    }
}


@respx.mock
class TestQuotaCLI:
    """Integration tests for quota CLI commands."""

    def test_quota_reservations_create(self):
        """Test creating a reservation via CLI."""
        runner = CliRunner()
        # Create temporary file with request JSON
        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.json',
                                         delete=False) as f:
            json.dump(TEST_RESERVATION_REQUEST, f)
            temp_file = f.name
        try:
            route = respx.post(f"{TEST_URL}/reservations")
            route.return_value = httpx.Response(HTTPStatus.CREATED,
                                                json=TEST_RESERVATION_RESPONSE)
            result = runner.invoke(
                quota,
                ['--base-url', TEST_URL, 'reservations', 'create', temp_file])
            assert result.exit_code == 0
            assert route.call_count == 1
            # Verify output contains reservation ID
            output_json = json.loads(result.output)
            assert output_json['id'] == TEST_RESERVATION_RESPONSE['id']
        finally:
            import os
            os.unlink(temp_file)

    def test_quota_reservations_list(self):
        """Test listing reservations via CLI."""
        runner = CliRunner()
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        result = runner.invoke(
            quota, ['--base-url', TEST_URL, 'reservations', 'list'])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify output contains reservation data
        output_json = json.loads(result.output)
        assert len(output_json) == 1
        assert output_json[0]['id'] == TEST_RESERVATION_RESPONSE['id']

    def test_quota_reservations_list_with_status(self):
        """Test listing reservations with status filter via CLI."""
        runner = CliRunner()
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        result = runner.invoke(quota,
                               [
                                   '--base-url',
                                   TEST_URL,
                                   'reservations',
                                   'list',
                                   '--status',
                                   'active'
                               ])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify status parameter was sent
        request = route.calls[0].request
        assert "status=active" in str(request.url)

    def test_quota_reservations_list_compact(self):
        """Test listing reservations with compact output via CLI."""
        runner = CliRunner()
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        result = runner.invoke(
            quota,
            ['--base-url', TEST_URL, 'reservations', 'list', '--compact'])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify compact output only contains expected fields
        output_json = json.loads(result.output)
        assert len(output_json) == 1
        compact_fields = {'id', 'name', 'status', 'created_at'}
        actual_fields = set(output_json[0].keys())
        assert actual_fields == compact_fields

    def test_quota_reservations_get(self):
        """Test getting a specific reservation via CLI."""
        runner = CliRunner()
        reservation_id = "12345678-1234-5678-9012-123456789012"
        route = respx.get(f"{TEST_URL}/reservations/{reservation_id}")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATION_RESPONSE)
        result = runner.invoke(
            quota,
            ['--base-url', TEST_URL, 'reservations', 'get', reservation_id])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify output contains reservation data
        output_json = json.loads(result.output)
        assert output_json['id'] == reservation_id

    def test_quota_reservations_cancel(self):
        """Test cancelling a reservation via CLI."""
        runner = CliRunner()
        reservation_id = "12345678-1234-5678-9012-123456789012"
        cancelled_response = {
            **TEST_RESERVATION_RESPONSE, "status": "cancelled"
        }
        route = respx.post(f"{TEST_URL}/reservations/{reservation_id}/cancel")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=cancelled_response)
        result = runner.invoke(
            quota,
            ['--base-url', TEST_URL, 'reservations', 'cancel', reservation_id])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify output shows cancelled status
        output_json = json.loads(result.output)
        assert output_json['status'] == 'cancelled'

    def test_quota_estimate(self):
        """Test estimating quota via CLI."""
        runner = CliRunner()
        # Create temporary file with estimation request JSON
        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.json',
                                         delete=False) as f:
            json.dump(TEST_RESERVATION_REQUEST, f)
            temp_file = f.name
        try:
            route = respx.post(f"{TEST_URL}/estimate")
            route.return_value = httpx.Response(HTTPStatus.OK,
                                                json=TEST_ESTIMATE_RESPONSE)
            result = runner.invoke(
                quota, ['--base-url', TEST_URL, 'estimate', temp_file])
            assert result.exit_code == 0
            assert route.call_count == 1
            # Verify output contains estimation data
            output_json = json.loads(result.output)
            assert output_json['estimated_cost'] == 100.0
        finally:
            import os
            os.unlink(temp_file)

    def test_quota_usage(self):
        """Test getting quota usage via CLI."""
        runner = CliRunner()
        route = respx.get(f"{TEST_URL}/usage")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_QUOTA_USAGE)
        result = runner.invoke(quota, ['--base-url', TEST_URL, 'usage'])
        assert result.exit_code == 0
        assert route.call_count == 1
        # Verify output contains usage data
        output_json = json.loads(result.output)
        assert 'current_usage' in output_json
        assert 'quota_limits' in output_json
