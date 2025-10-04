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
import httpx
import pytest
import respx
from planet import QuotaClient, Session
from planet.auth import Auth
from planet.sync.quota import QuotaAPI

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
    "created_at": "2025-01-01T00:00:00Z",
    "products": ["PSScene"],
    "item_types": ["PSScene4Band"]
}
TEST_ESTIMATE_RESPONSE = {
    "estimated_cost": 100.0,
    "estimated_usage": {
        "area_km2": 25.0, "item_count": 10
    }
}
TEST_RESERVATIONS_LIST = {
    "reservations": [TEST_RESERVATION_RESPONSE], "_next": None
}
TEST_QUOTA_USAGE = {
    "current_usage": {
        "area_km2": 150.0, "item_count": 50
    },
    "quota_limits": {
        "area_km2": 1000.0, "item_count": 500
    }
}
# Set up test clients
test_session = Session(auth=Auth.from_key(key="test"))


@respx.mock
class TestQuotaClientIntegration:
    """Integration tests for QuotaClient with mocked HTTP responses."""

    async def test_create_reservation(self):
        """Test creating a quota reservation."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        route = respx.post(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.CREATED,
                                            json=TEST_RESERVATION_RESPONSE)
        result = await client.create_reservation(TEST_RESERVATION_REQUEST)
        assert result == TEST_RESERVATION_RESPONSE
        assert route.call_count == 1
        # Verify request payload
        request = route.calls[0].request
        assert json.loads(request.content) == TEST_RESERVATION_REQUEST

    async def test_estimate_quota(self):
        """Test estimating quota requirements."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        route = respx.post(f"{TEST_URL}/estimate")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_ESTIMATE_RESPONSE)
        result = await client.estimate_quota(TEST_RESERVATION_REQUEST)
        assert result == TEST_ESTIMATE_RESPONSE
        assert route.call_count == 1

    async def test_list_reservations(self):
        """Test listing quota reservations."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        reservations = []
        async for reservation in client.list_reservations():
            reservations.append(reservation)
        assert len(reservations) == 1
        assert reservations[0] == TEST_RESERVATION_RESPONSE
        assert route.call_count == 1

    async def test_list_reservations_with_status_filter(self):
        """Test listing quota reservations with status filter."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        reservations = []
        async for reservation in client.list_reservations(status="active"):
            reservations.append(reservation)
        assert len(reservations) == 1
        assert route.call_count == 1
        # Verify status parameter was sent
        request = route.calls[0].request
        assert "status=active" in str(request.url)

    async def test_get_reservation(self):
        """Test getting a specific quota reservation."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        reservation_id = "12345678-1234-5678-9012-123456789012"
        route = respx.get(f"{TEST_URL}/reservations/{reservation_id}")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATION_RESPONSE)
        result = await client.get_reservation(reservation_id)
        assert result == TEST_RESERVATION_RESPONSE
        assert route.call_count == 1

    async def test_cancel_reservation(self):
        """Test cancelling a quota reservation."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        reservation_id = "12345678-1234-5678-9012-123456789012"
        cancelled_response = {
            **TEST_RESERVATION_RESPONSE, "status": "cancelled"
        }
        route = respx.post(f"{TEST_URL}/reservations/{reservation_id}/cancel")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=cancelled_response)
        result = await client.cancel_reservation(reservation_id)
        assert result["status"] == "cancelled"
        assert route.call_count == 1

    async def test_get_quota_usage(self):
        """Test getting quota usage statistics."""
        client = QuotaClient(test_session, base_url=TEST_URL)
        route = respx.get(f"{TEST_URL}/usage")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_QUOTA_USAGE)
        result = await client.get_quota_usage()
        assert result == TEST_QUOTA_USAGE
        assert route.call_count == 1


@respx.mock
class TestQuotaAPIIntegration:
    """Integration tests for synchronous QuotaAPI."""

    def test_create_reservation_sync(self):
        """Test creating a quota reservation using sync API."""
        api = QuotaAPI(test_session, base_url=TEST_URL)
        route = respx.post(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.CREATED,
                                            json=TEST_RESERVATION_RESPONSE)
        result = api.create_reservation(TEST_RESERVATION_REQUEST)
        assert result == TEST_RESERVATION_RESPONSE
        assert route.call_count == 1

    def test_list_reservations_sync(self):
        """Test listing quota reservations using sync API."""
        api = QuotaAPI(test_session, base_url=TEST_URL)
        route = respx.get(f"{TEST_URL}/reservations")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_RESERVATIONS_LIST)
        reservations = list(api.list_reservations())
        assert len(reservations) == 1
        assert reservations[0] == TEST_RESERVATION_RESPONSE
        assert route.call_count == 1

    def test_get_quota_usage_sync(self):
        """Test getting quota usage using sync API."""
        api = QuotaAPI(test_session, base_url=TEST_URL)
        route = respx.get(f"{TEST_URL}/usage")
        route.return_value = httpx.Response(HTTPStatus.OK,
                                            json=TEST_QUOTA_USAGE)
        result = api.get_quota_usage()
        assert result == TEST_QUOTA_USAGE
        assert route.call_count == 1
