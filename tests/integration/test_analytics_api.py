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
"""Integration tests for the Analytics API."""

from http import HTTPStatus
import httpx
import pytest
import respx

from planet.clients.analytics import AnalyticsClient
from planet import Session
from planet.auth import Auth
from planet.sync.analytics import AnalyticsAPI

pytestmark = pytest.mark.anyio  # noqa

# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.planet.com/analytics/v1"

TEST_FEED_1 = {
    "id": "feed1",
    "name": "Test Feed 1",
    "description": "A test analytics feed",
    "type": "detections"
}

TEST_FEED_2 = {
    "id": "feed2",
    "name": "Test Feed 2",
    "description": "Another test analytics feed",
    "type": "classifications"
}

TEST_SUBSCRIPTION_1 = {
    "id": "sub1",
    "feed_id": "feed1",
    "status": "active",
    "created": "2023-01-01T00:00:00Z"
}

TEST_SUBSCRIPTION_2 = {
    "id": "sub2",
    "feed_id": "feed2",
    "status": "active",
    "created": "2023-01-02T00:00:00Z"
}

TEST_RESULT_1 = {
    "id": "result1",
    "feed_id": "feed1",
    "subscription_id": "sub1",
    "timestamp": "2023-01-01T12:00:00Z",
    "geometry": {
        "type": "Point", "coordinates": [-122.4, 37.8]
    }
}

TEST_RESULT_2 = {
    "id": "result2",
    "feed_id": "feed1",
    "subscription_id": "sub1",
    "timestamp": "2023-01-02T12:00:00Z",
    "geometry": {
        "type": "Point", "coordinates": [-122.5, 37.9]
    }
}

TEST_FEED_STATS = {
    "feed_id": "feed1",
    "total_results": 2,
    "date_range": {
        "start": "2023-01-01T00:00:00Z", "end": "2023-01-02T23:59:59Z"
    }
}

# Set up test clients
test_session = Session(auth=Auth.from_key(key="test"))
test_analytics_client = AnalyticsClient(test_session, base_url=TEST_URL)
test_analytics_api = AnalyticsAPI(test_session, base_url=TEST_URL)


@respx.mock
class TestAnalyticsClientIntegration:
    """Integration tests for AnalyticsClient."""

    async def test_list_feeds(self):
        """Test listing analytics feeds."""
        feeds_route = respx.get(f"{TEST_URL}/feeds").mock(
            return_value=httpx.Response(
                HTTPStatus.OK, json={"feeds": [TEST_FEED_1, TEST_FEED_2]}))

        feeds = []
        async for feed in test_analytics_client.list_feeds():
            feeds.append(feed)

        assert len(feeds) == 2
        assert feeds[0]["id"] == "feed1"
        assert feeds[1]["id"] == "feed2"
        assert feeds_route.called

    async def test_list_feeds_with_limit(self):
        """Test listing analytics feeds with limit."""
        feeds_route = respx.get(f"{TEST_URL}/feeds").mock(
            return_value=httpx.Response(HTTPStatus.OK,
                                        json={"feeds": [TEST_FEED_1]}))

        feeds = []
        async for feed in test_analytics_client.list_feeds(limit=1):
            feeds.append(feed)

        assert len(feeds) == 1
        assert feeds[0]["id"] == "feed1"
        assert feeds_route.called

    async def test_get_feed(self):
        """Test getting a specific analytics feed."""
        feed_route = respx.get(f"{TEST_URL}/feeds/feed1").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_FEED_1))

        feed = await test_analytics_client.get_feed("feed1")

        assert feed["id"] == "feed1"
        assert feed["name"] == "Test Feed 1"
        assert feed_route.called

    async def test_list_subscriptions(self):
        """Test listing analytics subscriptions."""
        subs_route = respx.get(
            f"{TEST_URL}/subscriptions"
        ).mock(return_value=httpx.Response(
            HTTPStatus.OK,
            json={"subscriptions": [TEST_SUBSCRIPTION_1, TEST_SUBSCRIPTION_2]
                  }))

        subscriptions = []
        async for subscription in test_analytics_client.list_subscriptions():
            subscriptions.append(subscription)

        assert len(subscriptions) == 2
        assert subscriptions[0]["id"] == "sub1"
        assert subscriptions[1]["id"] == "sub2"
        assert subs_route.called

    async def test_list_subscriptions_with_feed_id(self):
        """Test listing analytics subscriptions filtered by feed ID."""
        subs_route = respx.get(f"{TEST_URL}/subscriptions").mock(
            return_value=httpx.Response(
                HTTPStatus.OK, json={"subscriptions": [TEST_SUBSCRIPTION_1]}))

        subscriptions = []
        async for subscription in test_analytics_client.list_subscriptions(
                feed_id="feed1"):
            subscriptions.append(subscription)

        assert len(subscriptions) == 1
        assert subscriptions[0]["id"] == "sub1"
        assert subscriptions[0]["feed_id"] == "feed1"
        assert subs_route.called

    async def test_get_subscription(self):
        """Test getting a specific analytics subscription."""
        sub_route = respx.get(f"{TEST_URL}/subscriptions/sub1").mock(
            return_value=httpx.Response(HTTPStatus.OK,
                                        json=TEST_SUBSCRIPTION_1))

        subscription = await test_analytics_client.get_subscription("sub1")

        assert subscription["id"] == "sub1"
        assert subscription["feed_id"] == "feed1"
        assert subscription["status"] == "active"
        assert sub_route.called

    async def test_search_results(self):
        """Test searching analytics results."""
        results_route = respx.get(f"{TEST_URL}/results/search").mock(
            return_value=httpx.Response(
                HTTPStatus.OK,
                json={"results": [TEST_RESULT_1, TEST_RESULT_2]}))

        results = []
        async for result in test_analytics_client.search_results("feed1"):
            results.append(result)

        assert len(results) == 2
        assert results[0]["id"] == "result1"
        assert results[1]["id"] == "result2"
        assert results_route.called

    async def test_search_results_with_params(self):
        """Test searching analytics results with parameters."""
        results_route = respx.get(f"{TEST_URL}/results/search").mock(
            return_value=httpx.Response(HTTPStatus.OK,
                                        json={"results": [TEST_RESULT_1]}))

        results = []
        async for result in test_analytics_client.search_results(
                feed_id="feed1",
                subscription_id="sub1",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T23:59:59Z",
                bbox=[-122.5, 37.7, -122.3, 37.9]):
            results.append(result)

        assert len(results) == 1
        assert results[0]["id"] == "result1"
        assert results_route.called

    async def test_search_results_with_geometry(self):
        """Test searching analytics results with geometry."""
        geometry = {"type": "Point", "coordinates": [-122.4, 37.8]}

        results_route = respx.post(f"{TEST_URL}/results/search").mock(
            return_value=httpx.Response(HTTPStatus.OK,
                                        json={"results": [TEST_RESULT_1]}))

        results = []
        async for result in test_analytics_client.search_results(
                feed_id="feed1", geometry=geometry):
            results.append(result)

        assert len(results) == 1
        assert results[0]["id"] == "result1"
        assert results_route.called

    async def test_get_result(self):
        """Test getting a specific analytics result."""
        result_route = respx.get(f"{TEST_URL}/results/result1").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_RESULT_1))

        result = await test_analytics_client.get_result("result1")

        assert result["id"] == "result1"
        assert result["feed_id"] == "feed1"
        assert result["timestamp"] == "2023-01-01T12:00:00Z"
        assert result_route.called

    async def test_download_result_json(self):
        """Test downloading analytics result in JSON format."""
        download_data = {"features": [{"type": "Feature", "id": "result1"}]}

        download_route = respx.get(
            f"{TEST_URL}/results/result1/download").mock(
                return_value=httpx.Response(HTTPStatus.OK, json=download_data))

        data = await test_analytics_client.download_result("result1", "json")

        assert data == download_data
        assert download_route.called

    async def test_download_result_csv(self):
        """Test downloading analytics result in CSV format."""
        csv_data = "id,timestamp,value\nresult1,2023-01-01T12:00:00Z,100"

        download_route = respx.get(
            f"{TEST_URL}/results/result1/download").mock(
                return_value=httpx.Response(HTTPStatus.OK, content=csv_data))

        data = await test_analytics_client.download_result("result1", "csv")

        assert data == csv_data
        assert download_route.called

    async def test_get_feed_stats(self):
        """Test getting analytics feed statistics."""
        stats_route = respx.get(f"{TEST_URL}/feeds/feed1/stats").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_FEED_STATS))

        stats = await test_analytics_client.get_feed_stats("feed1")

        assert stats["feed_id"] == "feed1"
        assert stats["total_results"] == 2
        assert stats_route.called

    async def test_get_feed_stats_with_params(self):
        """Test getting analytics feed statistics with parameters."""
        stats_route = respx.get(f"{TEST_URL}/feeds/feed1/stats").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_FEED_STATS))

        stats = await test_analytics_client.get_feed_stats(
            "feed1",
            subscription_id="sub1",
            start_time="2023-01-01T00:00:00Z",
            end_time="2023-01-01T23:59:59Z")

        assert stats["feed_id"] == "feed1"
        assert stats["total_results"] == 2
        assert stats_route.called


@respx.mock
class TestAnalyticsAPIIntegration:
    """Integration tests for synchronous AnalyticsAPI."""

    def test_list_feeds(self):
        """Test listing analytics feeds (sync)."""
        feeds_route = respx.get(f"{TEST_URL}/feeds").mock(
            return_value=httpx.Response(
                HTTPStatus.OK, json={"feeds": [TEST_FEED_1, TEST_FEED_2]}))

        feeds = list(test_analytics_api.list_feeds())

        assert len(feeds) == 2
        assert feeds[0]["id"] == "feed1"
        assert feeds[1]["id"] == "feed2"
        assert feeds_route.called

    def test_get_feed(self):
        """Test getting a specific analytics feed (sync)."""
        feed_route = respx.get(f"{TEST_URL}/feeds/feed1").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_FEED_1))

        feed = test_analytics_api.get_feed("feed1")

        assert feed["id"] == "feed1"
        assert feed["name"] == "Test Feed 1"
        assert feed_route.called

    def test_list_subscriptions(self):
        """Test listing analytics subscriptions (sync)."""
        subs_route = respx.get(
            f"{TEST_URL}/subscriptions"
        ).mock(return_value=httpx.Response(
            HTTPStatus.OK,
            json={"subscriptions": [TEST_SUBSCRIPTION_1, TEST_SUBSCRIPTION_2]
                  }))

        subscriptions = list(test_analytics_api.list_subscriptions())

        assert len(subscriptions) == 2
        assert subscriptions[0]["id"] == "sub1"
        assert subscriptions[1]["id"] == "sub2"
        assert subs_route.called

    def test_get_subscription(self):
        """Test getting a specific analytics subscription (sync)."""
        sub_route = respx.get(f"{TEST_URL}/subscriptions/sub1").mock(
            return_value=httpx.Response(HTTPStatus.OK,
                                        json=TEST_SUBSCRIPTION_1))

        subscription = test_analytics_api.get_subscription("sub1")

        assert subscription["id"] == "sub1"
        assert subscription["feed_id"] == "feed1"
        assert subscription["status"] == "active"
        assert sub_route.called

    def test_search_results(self):
        """Test searching analytics results (sync)."""
        results_route = respx.get(f"{TEST_URL}/results/search").mock(
            return_value=httpx.Response(
                HTTPStatus.OK,
                json={"results": [TEST_RESULT_1, TEST_RESULT_2]}))

        results = list(test_analytics_api.search_results("feed1"))

        assert len(results) == 2
        assert results[0]["id"] == "result1"
        assert results[1]["id"] == "result2"
        assert results_route.called

    def test_get_result(self):
        """Test getting a specific analytics result (sync)."""
        result_route = respx.get(f"{TEST_URL}/results/result1").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_RESULT_1))

        result = test_analytics_api.get_result("result1")

        assert result["id"] == "result1"
        assert result["feed_id"] == "feed1"
        assert result["timestamp"] == "2023-01-01T12:00:00Z"
        assert result_route.called

    def test_download_result(self):
        """Test downloading analytics result (sync)."""
        download_data = {"features": [{"type": "Feature", "id": "result1"}]}

        download_route = respx.get(
            f"{TEST_URL}/results/result1/download").mock(
                return_value=httpx.Response(HTTPStatus.OK, json=download_data))

        data = test_analytics_api.download_result("result1", "json")

        assert data == download_data
        assert download_route.called

    def test_get_feed_stats(self):
        """Test getting analytics feed statistics (sync)."""
        stats_route = respx.get(f"{TEST_URL}/feeds/feed1/stats").mock(
            return_value=httpx.Response(HTTPStatus.OK, json=TEST_FEED_STATS))

        stats = test_analytics_api.get_feed_stats("feed1")

        assert stats["feed_id"] == "feed1"
        assert stats["total_results"] == 2
        assert stats_route.called
