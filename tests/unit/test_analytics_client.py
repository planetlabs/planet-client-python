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
"""Tests for the Analytics API client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from planet.clients.analytics import AnalyticsClient
from planet.exceptions import ClientError
from planet.http import Session

pytestmark = pytest.mark.anyio  # noqa


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    session.request = AsyncMock()
    return session


@pytest.fixture
def analytics_client(mock_session):
    return AnalyticsClient(mock_session)


class TestAnalyticsClient:
    """Test cases for the AnalyticsClient."""

    def test_analytics_client_initialization(self, mock_session):
        """Test that AnalyticsClient initializes correctly."""
        client = AnalyticsClient(mock_session)
        assert client._session is mock_session
        assert client._base_url == "https://api.planet.com/analytics/v1"

    def test_analytics_client_custom_base_url(self, mock_session):
        """Test that AnalyticsClient accepts custom base URL."""
        custom_url = "https://custom.planet.com/analytics/v1"
        client = AnalyticsClient(mock_session, base_url=custom_url)
        assert client._base_url == custom_url

    async def test_get_feed(self, analytics_client, mock_session):
        """Test get_feed method."""
        feed_data = {
            "id": "test-feed",
            "name": "Test Feed",
            "description": "A test analytics feed"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = feed_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.get_feed("test-feed")

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/feeds/test-feed')
        assert result == feed_data

    async def test_list_feeds(self, analytics_client, mock_session):
        """Test list_feeds method."""
        feeds_data = {
            "feeds": [{
                "id": "feed1", "name": "Feed 1"
            }, {
                "id": "feed2", "name": "Feed 2"
            }]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = feeds_data
        mock_session.request.return_value = mock_response

        feeds = []
        async for feed in analytics_client.list_feeds():
            feeds.append(feed)

        mock_session.request.assert_called_once_with(
            method='GET', url='https://api.planet.com/analytics/v1/feeds')

    async def test_get_subscription(self, analytics_client, mock_session):
        """Test get_subscription method."""
        subscription_data = {
            "id": "test-subscription",
            "feed_id": "test-feed",
            "status": "active"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = subscription_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.get_subscription("test-subscription")

        mock_session.request.assert_called_once_with(
            method='GET',
            url=
            'https://api.planet.com/analytics/v1/subscriptions/test-subscription'
        )
        assert result == subscription_data

    async def test_list_subscriptions(self, analytics_client, mock_session):
        """Test list_subscriptions method."""
        subscriptions_data = {
            "subscriptions": [{
                "id": "sub1", "feed_id": "feed1"
            }, {
                "id": "sub2", "feed_id": "feed2"
            }]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = subscriptions_data
        mock_session.request.return_value = mock_response

        subscriptions = []
        async for subscription in analytics_client.list_subscriptions():
            subscriptions.append(subscription)

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/subscriptions',
            params={})

    async def test_list_subscriptions_with_feed_id(self,
                                                   analytics_client,
                                                   mock_session):
        """Test list_subscriptions method with feed_id filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"subscriptions": []}
        mock_session.request.return_value = mock_response

        subscriptions = []
        async for subscription in analytics_client.list_subscriptions(
                feed_id="test-feed"):
            subscriptions.append(subscription)

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/subscriptions',
            params={'feed_id': 'test-feed'})

    async def test_search_results(self, analytics_client, mock_session):
        """Test search_results method."""
        results_data = {
            "results": [{
                "id": "result1", "timestamp": "2023-01-01T00:00:00Z"
            }, {
                "id": "result2", "timestamp": "2023-01-02T00:00:00Z"
            }]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = results_data
        mock_session.request.return_value = mock_response

        results = []
        async for result in analytics_client.search_results("test-feed"):
            results.append(result)

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/results/search',
            params={'feed_id': 'test-feed'},
            json=None)

    async def test_search_results_with_params(self,
                                              analytics_client,
                                              mock_session):
        """Test search_results method with all parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_session.request.return_value = mock_response

        results = []
        async for result in analytics_client.search_results(
                feed_id="test-feed",
                subscription_id="test-sub",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-31T23:59:59Z",
                bbox=[-122.5, 37.7, -122.3, 37.8]):
            results.append(result)

        expected_params = {
            'feed_id': 'test-feed',
            'subscription_id': 'test-sub',
            'start_time': '2023-01-01T00:00:00Z',
            'end_time': '2023-01-31T23:59:59Z',
            'bbox': '-122.5,37.7,-122.3,37.8'
        }

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/results/search',
            params=expected_params,
            json=None)

    async def test_search_results_with_geometry(self,
                                                analytics_client,
                                                mock_session):
        """Test search_results method with geometry parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_session.request.return_value = mock_response

        geometry = {"type": "Point", "coordinates": [-122.4, 37.8]}

        results = []
        async for result in analytics_client.search_results(
                feed_id="test-feed", geometry=geometry):
            results.append(result)

        mock_session.request.assert_called_once_with(
            method='POST',
            url='https://api.planet.com/analytics/v1/results/search',
            params={'feed_id': 'test-feed'},
            json={'geometry': geometry})

    async def test_search_results_invalid_bbox(self, analytics_client):
        """Test search_results method with invalid bbox."""
        with pytest.raises(ClientError,
                           match="bbox must contain exactly 4 values"):
            async for _ in analytics_client.search_results(
                    feed_id="test-feed",
                    bbox=[-122.5, 37.7, -122.3]  # Only 3 values
            ):
                pass

    async def test_get_result(self, analytics_client, mock_session):
        """Test get_result method."""
        result_data = {
            "id": "test-result",
            "timestamp": "2023-01-01T00:00:00Z",
            "data": {
                "detections": []
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = result_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.get_result("test-result")

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/results/test-result')
        assert result == result_data

    async def test_download_result_json(self, analytics_client, mock_session):
        """Test download_result method with JSON format."""
        result_data = {"features": [{"type": "Feature"}]}

        mock_response = MagicMock()
        mock_response.json.return_value = result_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.download_result("test-result", "json")

        mock_session.request.assert_called_once_with(
            method='GET',
            url=
            'https://api.planet.com/analytics/v1/results/test-result/download',
            params={'format': 'json'})
        assert result == result_data

    async def test_download_result_csv(self, analytics_client, mock_session):
        """Test download_result method with CSV format."""
        csv_data = "id,timestamp,value\n1,2023-01-01,100"

        mock_response = MagicMock()
        mock_response.text.return_value = csv_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.download_result("test-result", "csv")

        mock_session.request.assert_called_once_with(
            method='GET',
            url=
            'https://api.planet.com/analytics/v1/results/test-result/download',
            params={'format': 'csv'})
        assert result == csv_data

    async def test_get_feed_stats(self, analytics_client, mock_session):
        """Test get_feed_stats method."""
        stats_data = {
            "feed_id": "test-feed",
            "total_results": 1000,
            "date_range": {
                "start": "2023-01-01T00:00:00Z", "end": "2023-01-31T23:59:59Z"
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = stats_data
        mock_session.request.return_value = mock_response

        result = await analytics_client.get_feed_stats("test-feed")

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/feeds/test-feed/stats',
            params={})
        assert result == stats_data

    async def test_get_feed_stats_with_params(self,
                                              analytics_client,
                                              mock_session):
        """Test get_feed_stats method with parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"total_results": 500}
        mock_session.request.return_value = mock_response

        await analytics_client.get_feed_stats(
            "test-feed",
            subscription_id="test-sub",
            start_time="2023-01-01T00:00:00Z",
            end_time="2023-01-31T23:59:59Z")

        expected_params = {
            'subscription_id': 'test-sub',
            'start_time': '2023-01-01T00:00:00Z',
            'end_time': '2023-01-31T23:59:59Z'
        }

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/analytics/v1/feeds/test-feed/stats',
            params=expected_params)
