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
"""Tests for the synchronous Analytics API."""

from unittest.mock import MagicMock, patch

import pytest

from planet.sync.analytics import AnalyticsAPI
from planet.clients.analytics import AnalyticsClient
from planet.http import Session


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def analytics_api(mock_session):
    return AnalyticsAPI(mock_session)


class TestAnalyticsAPI:
    """Test cases for the synchronous AnalyticsAPI."""

    def test_analytics_api_initialization(self, mock_session):
        """Test that AnalyticsAPI initializes correctly."""
        api = AnalyticsAPI(mock_session)
        assert isinstance(api._client, AnalyticsClient)
        assert api._client._session is mock_session
        assert api._client._base_url == "https://api.planet.com/analytics/v1"

    def test_analytics_api_custom_base_url(self, mock_session):
        """Test that AnalyticsAPI accepts custom base URL."""
        custom_url = "https://custom.planet.com/analytics/v1"
        api = AnalyticsAPI(mock_session, base_url=custom_url)
        assert api._client._base_url == custom_url

    def test_list_feeds(self, analytics_api):
        """Test list_feeds method."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter([{
                "id": "feed1", "name": "Feed 1"
            }, {
                "id": "feed2", "name": "Feed 2"
            }])

            feeds = list(analytics_api.list_feeds())

            assert len(feeds) == 2
            assert feeds[0]["id"] == "feed1"
            assert feeds[1]["id"] == "feed2"

            # Verify the async method was called correctly
            mock_aiter.assert_called_once()

    def test_list_feeds_with_limit(self, analytics_api):
        """Test list_feeds method with limit."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter([{"id": "feed1"}])

            list(analytics_api.list_feeds(limit=10))

            mock_aiter.assert_called_once()

    def test_get_feed(self, analytics_api):
        """Test get_feed method."""
        feed_data = {"id": "test-feed", "name": "Test Feed"}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = feed_data

            result = analytics_api.get_feed("test-feed")

            assert result == feed_data
            mock_call_sync.assert_called_once()

    def test_list_subscriptions(self, analytics_api):
        """Test list_subscriptions method."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter([{
                "id": "sub1", "feed_id": "feed1"
            }, {
                "id": "sub2", "feed_id": "feed2"
            }])

            subscriptions = list(analytics_api.list_subscriptions())

            assert len(subscriptions) == 2
            assert subscriptions[0]["id"] == "sub1"
            assert subscriptions[1]["id"] == "sub2"

    def test_list_subscriptions_with_feed_id(self, analytics_api):
        """Test list_subscriptions method with feed_id filter."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter([{
                "id": "sub1", "feed_id": "feed1"
            }])

            list(analytics_api.list_subscriptions(feed_id="feed1"))

            mock_aiter.assert_called_once()

    def test_get_subscription(self, analytics_api):
        """Test get_subscription method."""
        subscription_data = {"id": "test-sub", "status": "active"}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = subscription_data

            result = analytics_api.get_subscription("test-sub")

            assert result == subscription_data
            mock_call_sync.assert_called_once()

    def test_search_results(self, analytics_api):
        """Test search_results method."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter(
                [{
                    "id": "result1", "timestamp": "2023-01-01T00:00:00Z"
                }, {
                    "id": "result2", "timestamp": "2023-01-02T00:00:00Z"
                }])

            results = list(analytics_api.search_results("test-feed"))

            assert len(results) == 2
            assert results[0]["id"] == "result1"
            assert results[1]["id"] == "result2"

    def test_search_results_with_params(self, analytics_api):
        """Test search_results method with all parameters."""
        with patch.object(analytics_api._client,
                          '_aiter_to_iter') as mock_aiter:
            mock_aiter.return_value = iter([])

            list(
                analytics_api.search_results(feed_id="test-feed",
                                             subscription_id="test-sub",
                                             start_time="2023-01-01T00:00:00Z",
                                             end_time="2023-01-31T23:59:59Z",
                                             bbox=[-122.5, 37.7, -122.3, 37.8],
                                             geometry={
                                                 "type": "Point",
                                                 "coordinates": [-122.4, 37.8]
                                             },
                                             limit=100))

            mock_aiter.assert_called_once()

    def test_get_result(self, analytics_api):
        """Test get_result method."""
        result_data = {
            "id": "test-result", "timestamp": "2023-01-01T00:00:00Z"
        }

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = result_data

            result = analytics_api.get_result("test-result")

            assert result == result_data
            mock_call_sync.assert_called_once()

    def test_download_result(self, analytics_api):
        """Test download_result method."""
        download_data = {"features": [{"type": "Feature"}]}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = download_data

            result = analytics_api.download_result("test-result", "geojson")

            assert result == download_data
            mock_call_sync.assert_called_once()

    def test_download_result_default_format(self, analytics_api):
        """Test download_result method with default format."""
        download_data = {"data": "test"}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = download_data

            result = analytics_api.download_result("test-result")

            assert result == download_data
            mock_call_sync.assert_called_once()

    def test_get_feed_stats(self, analytics_api):
        """Test get_feed_stats method."""
        stats_data = {"feed_id": "test-feed", "total_results": 1000}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = stats_data

            result = analytics_api.get_feed_stats("test-feed")

            assert result == stats_data
            mock_call_sync.assert_called_once()

    def test_get_feed_stats_with_params(self, analytics_api):
        """Test get_feed_stats method with parameters."""
        stats_data = {"feed_id": "test-feed", "total_results": 500}

        with patch.object(analytics_api._client,
                          '_call_sync') as mock_call_sync:
            mock_call_sync.return_value = stats_data

            result = analytics_api.get_feed_stats(
                "test-feed",
                subscription_id="test-sub",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-31T23:59:59Z")

            assert result == stats_data
            mock_call_sync.assert_called_once()
