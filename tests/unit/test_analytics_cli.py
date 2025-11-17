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
"""Tests for the Analytics CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from planet.cli.analytics import analytics


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.obj = {'BASE_URL': None}
    return ctx


class TestAnalyticsCLI:
    """Test cases for Analytics CLI commands."""

    def test_analytics_group(self, runner):
        """Test that analytics group command exists."""
        result = runner.invoke(analytics, ['--help'])
        assert result.exit_code == 0
        assert 'Commands for interacting with the Analytics API' in result.output

    def test_feeds_group(self, runner):
        """Test that feeds group command exists."""
        result = runner.invoke(analytics, ['feeds', '--help'])
        assert result.exit_code == 0
        assert 'Commands for interacting with Analytics feeds' in result.output

    def test_subscriptions_group(self, runner):
        """Test that subscriptions group command exists."""
        result = runner.invoke(analytics, ['subscriptions', '--help'])
        assert result.exit_code == 0
        assert 'Commands for interacting with Analytics subscriptions' in result.output

    def test_results_group(self, runner):
        """Test that results group command exists."""
        result = runner.invoke(analytics, ['results', '--help'])
        assert result.exit_code == 0
        assert 'Commands for interacting with Analytics results' in result.output

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_feeds_list(self, mock_echo_json, mock_client_ctx, runner):
        """Test feeds list command."""
        # Mock the client context manager
        mock_client = AsyncMock()
        mock_client.list_feeds = AsyncMock()
        mock_client.list_feeds.return_value.__aiter__ = AsyncMock(
            return_value=iter([{
                "id": "feed1", "name": "Feed 1"
            }, {
                "id": "feed2", "name": "Feed 2"
            }]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['feeds', 'list'])

        assert result.exit_code == 0
        # Verify that echo_json was called for each feed
        assert mock_echo_json.call_count == 2

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_feeds_list_with_limit(self,
                                   mock_echo_json,
                                   mock_client_ctx,
                                   runner):
        """Test feeds list command with limit."""
        mock_client = AsyncMock()
        mock_client.list_feeds = AsyncMock()
        mock_client.list_feeds.return_value.__aiter__ = AsyncMock(
            return_value=iter([{
                "id": "feed1", "name": "Feed 1"
            }]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['feeds', 'list', '--limit', '1'])

        assert result.exit_code == 0
        mock_client.list_feeds.assert_called_once_with(limit=1)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_feeds_get(self, mock_echo_json, mock_client_ctx, runner):
        """Test feeds get command."""
        feed_data = {"id": "test-feed", "name": "Test Feed"}

        mock_client = AsyncMock()
        mock_client.get_feed = AsyncMock(return_value=feed_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['feeds', 'get', 'test-feed'])

        assert result.exit_code == 0
        mock_client.get_feed.assert_called_once_with('test-feed')
        mock_echo_json.assert_called_once_with(feed_data, False)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_feeds_stats(self, mock_echo_json, mock_client_ctx, runner):
        """Test feeds stats command."""
        stats_data = {"feed_id": "test-feed", "total_results": 1000}

        mock_client = AsyncMock()
        mock_client.get_feed_stats = AsyncMock(return_value=stats_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['feeds', 'stats', 'test-feed'])

        assert result.exit_code == 0
        mock_client.get_feed_stats.assert_called_once_with(
            feed_id='test-feed',
            subscription_id=None,
            start_time=None,
            end_time=None)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_feeds_stats_with_params(self,
                                     mock_echo_json,
                                     mock_client_ctx,
                                     runner):
        """Test feeds stats command with parameters."""
        stats_data = {"feed_id": "test-feed", "total_results": 500}

        mock_client = AsyncMock()
        mock_client.get_feed_stats = AsyncMock(return_value=stats_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics,
                               [
                                   'feeds',
                                   'stats',
                                   'test-feed',
                                   '--subscription-id',
                                   'test-sub',
                                   '--start-time',
                                   '2023-01-01T00:00:00Z'
                               ])

        assert result.exit_code == 0
        mock_client.get_feed_stats.assert_called_once_with(
            feed_id='test-feed',
            subscription_id='test-sub',
            start_time='2023-01-01T00:00:00Z',
            end_time=None)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_subscriptions_list(self, mock_echo_json, mock_client_ctx, runner):
        """Test subscriptions list command."""
        mock_client = AsyncMock()
        mock_client.list_subscriptions = AsyncMock()
        mock_client.list_subscriptions.return_value.__aiter__ = AsyncMock(
            return_value=iter([{
                "id": "sub1", "feed_id": "feed1"
            }, {
                "id": "sub2", "feed_id": "feed2"
            }]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['subscriptions', 'list'])

        assert result.exit_code == 0
        mock_client.list_subscriptions.assert_called_once_with(feed_id=None,
                                                               limit=0)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_subscriptions_get(self, mock_echo_json, mock_client_ctx, runner):
        """Test subscriptions get command."""
        subscription_data = {"id": "test-sub", "status": "active"}

        mock_client = AsyncMock()
        mock_client.get_subscription = AsyncMock(
            return_value=subscription_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['subscriptions', 'get', 'test-sub'])

        assert result.exit_code == 0
        mock_client.get_subscription.assert_called_once_with('test-sub')

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_search(self, mock_echo_json, mock_client_ctx, runner):
        """Test results search command."""
        mock_client = AsyncMock()
        mock_client.search_results = AsyncMock()
        mock_client.search_results.return_value.__aiter__ = AsyncMock(
            return_value=iter([{
                "id": "result1", "timestamp": "2023-01-01T00:00:00Z"
            }]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['results', 'search', 'test-feed'])

        assert result.exit_code == 0
        mock_client.search_results.assert_called_once_with(
            feed_id='test-feed',
            subscription_id=None,
            start_time=None,
            end_time=None,
            bbox=None,
            geometry=None,
            limit=0)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_search_with_bbox(self,
                                      mock_echo_json,
                                      mock_client_ctx,
                                      runner):
        """Test results search command with bbox."""
        mock_client = AsyncMock()
        mock_client.search_results = AsyncMock()
        mock_client.search_results.return_value.__aiter__ = AsyncMock(
            return_value=iter([]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics,
                               [
                                   'results',
                                   'search',
                                   'test-feed',
                                   '--bbox',
                                   '-122.5,37.7,-122.3,37.8'
                               ])

        assert result.exit_code == 0
        mock_client.search_results.assert_called_once_with(
            feed_id='test-feed',
            subscription_id=None,
            start_time=None,
            end_time=None,
            bbox=[-122.5, 37.7, -122.3, 37.8],
            geometry=None,
            limit=0)

    def test_results_search_invalid_bbox(self, runner):
        """Test results search command with invalid bbox."""
        result = runner.invoke(
            analytics,
            [
                'results',
                'search',
                'test-feed',
                '--bbox',
                '-122.5,37.7,37.8'  # Only 3 values
            ])

        assert result.exit_code != 0
        assert 'Invalid bbox format' in result.output

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_search_with_geometry(self,
                                          mock_echo_json,
                                          mock_client_ctx,
                                          runner):
        """Test results search command with geometry."""
        geometry = {"type": "Point", "coordinates": [-122.4, 37.8]}

        mock_client = AsyncMock()
        mock_client.search_results = AsyncMock()
        mock_client.search_results.return_value.__aiter__ = AsyncMock(
            return_value=iter([]))

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics,
                               [
                                   'results',
                                   'search',
                                   'test-feed',
                                   '--geometry',
                                   json.dumps(geometry)
                               ])

        assert result.exit_code == 0
        mock_client.search_results.assert_called_once_with(
            feed_id='test-feed',
            subscription_id=None,
            start_time=None,
            end_time=None,
            bbox=None,
            geometry=geometry,
            limit=0)

    def test_results_search_invalid_geometry(self, runner):
        """Test results search command with invalid geometry JSON."""
        result = runner.invoke(
            analytics,
            ['results', 'search', 'test-feed', '--geometry', 'invalid-json'])

        assert result.exit_code != 0
        assert 'Invalid geometry JSON' in result.output

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_get(self, mock_echo_json, mock_client_ctx, runner):
        """Test results get command."""
        result_data = {
            "id": "test-result", "timestamp": "2023-01-01T00:00:00Z"
        }

        mock_client = AsyncMock()
        mock_client.get_result = AsyncMock(return_value=result_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics, ['results', 'get', 'test-result'])

        assert result.exit_code == 0
        mock_client.get_result.assert_called_once_with('test-result')

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_download_json(self,
                                   mock_echo_json,
                                   mock_client_ctx,
                                   runner):
        """Test results download command with JSON format."""
        download_data = {"features": [{"type": "Feature"}]}

        mock_client = AsyncMock()
        mock_client.download_result = AsyncMock(return_value=download_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(analytics,
                               ['results', 'download', 'test-result'])

        assert result.exit_code == 0
        mock_client.download_result.assert_called_once_with(
            'test-result', 'json')
        mock_echo_json.assert_called_once_with(download_data, False)

    @patch('planet.cli.analytics.analytics_client')
    @patch('planet.cli.analytics.echo_json')
    def test_results_download_geojson(self,
                                      mock_echo_json,
                                      mock_client_ctx,
                                      runner):
        """Test results download command with GeoJSON format."""
        download_data = {"type": "FeatureCollection", "features": []}

        mock_client = AsyncMock()
        mock_client.download_result = AsyncMock(return_value=download_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(
            analytics,
            ['results', 'download', 'test-result', '--format', 'geojson'])

        assert result.exit_code == 0
        mock_client.download_result.assert_called_once_with(
            'test-result', 'geojson')
        mock_echo_json.assert_called_once_with(download_data, False)

    @patch('planet.cli.analytics.analytics_client')
    @patch('click.echo')
    def test_results_download_csv(self, mock_echo, mock_client_ctx, runner):
        """Test results download command with CSV format."""
        csv_data = "id,timestamp,value\n1,2023-01-01,100"

        mock_client = AsyncMock()
        mock_client.download_result = AsyncMock(return_value=csv_data)

        mock_client_ctx.return_value.__aenter__ = AsyncMock(
            return_value=mock_client)
        mock_client_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        result = runner.invoke(
            analytics,
            ['results', 'download', 'test-result', '--format', 'csv'])

        assert result.exit_code == 0
        mock_client.download_result.assert_called_once_with(
            'test-result', 'csv')
        mock_echo.assert_called_once_with(csv_data)
