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

from typing import Iterator, List, Optional, Union
from datetime import datetime

from planet.clients.analytics import AnalyticsClient
from planet.http import Session


class AnalyticsAPI:
    """Synchronous Analytics API client

    The Analytics API provides programmatic access to Planet Analytic Feeds
    that detect and classify objects, identify geographic features, and
    understand change over time across the globe.

    For more information about the Analytics API, see the documentation at
    https://docs.planet.com/develop/apis/analytics/

    Example:
        ```python
        >>> from planet.sync import Planet
        >>>
        >>> pl = Planet()
        >>> feeds = pl.analytics.list_feeds()
        >>> for feed in feeds:
        ...     print(feed)
        ```
    """

    _client: AnalyticsClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Analytics API
                base url.
        """
        self._client = AnalyticsClient(session, base_url)

    def list_feeds(self, limit: int = 0) -> Iterator[dict]:
        """
        List available analytics feeds.

        Parameters:
            limit: Maximum number of feeds to return. When set to 0, no
                maximum is applied.

        Returns:
            Iterator over analytics feeds.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            feeds = pl.analytics.list_feeds()
            for feed in feeds:
                print(f"Feed: {feed['id']} - {feed['name']}")
            ```
        """
        return self._client._aiter_to_iter(
            self._client.list_feeds(limit=limit))

    def get_feed(self, feed_id: str) -> dict:
        """
        Get details of a specific analytics feed.

        Parameters:
            feed_id: The ID of the analytics feed.

        Returns:
            Description of the analytics feed.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            feed = pl.analytics.get_feed("my-feed-id")
            print(f"Feed description: {feed['description']}")
            ```
        """
        return self._client._call_sync(self._client.get_feed(feed_id))

    def list_subscriptions(self,
                           feed_id: Optional[str] = None,
                           limit: int = 0) -> Iterator[dict]:
        """
        List analytics subscriptions.

        Parameters:
            feed_id: If provided, only list subscriptions for this feed.
            limit: Maximum number of subscriptions to return. When set to 0, no
                maximum is applied.

        Returns:
            Iterator over analytics subscriptions.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            subscriptions = pl.analytics.list_subscriptions()
            for subscription in subscriptions:
                print(f"Subscription: {subscription['id']}")
            ```
        """
        return self._client._aiter_to_iter(
            self._client.list_subscriptions(feed_id=feed_id, limit=limit))

    def get_subscription(self, subscription_id: str) -> dict:
        """
        Get details of a specific analytics subscription.

        Parameters:
            subscription_id: The ID of the analytics subscription.

        Returns:
            Description of the analytics subscription.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            subscription = pl.analytics.get_subscription("my-subscription-id")
            print(f"Subscription status: {subscription['status']}")
            ```
        """
        return self._client._call_sync(
            self._client.get_subscription(subscription_id))

    def search_results(self,
                       feed_id: str,
                       subscription_id: Optional[str] = None,
                       geometry: Optional[dict] = None,
                       start_time: Optional[Union[str, datetime]] = None,
                       end_time: Optional[Union[str, datetime]] = None,
                       bbox: Optional[List[float]] = None,
                       limit: int = 0) -> Iterator[dict]:
        """
        Search for analytics results.

        Parameters:
            feed_id: The ID of the analytics feed to search.
            subscription_id: If provided, only search results from this subscription.
            geometry: GeoJSON geometry to filter results by spatial intersection.
            start_time: Start time for temporal filtering (ISO 8601 string or datetime).
            end_time: End time for temporal filtering (ISO 8601 string or datetime).
            bbox: Bounding box as [west, south, east, north] to filter results.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.

        Returns:
            Iterator over analytics results.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            results = pl.analytics.search_results(
                feed_id="my-feed-id",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-31T23:59:59Z"
            )
            for result in results:
                print(f"Result: {result['id']}")
            ```
        """
        return self._client._aiter_to_iter(
            self._client.search_results(feed_id=feed_id,
                                        subscription_id=subscription_id,
                                        geometry=geometry,
                                        start_time=start_time,
                                        end_time=end_time,
                                        bbox=bbox,
                                        limit=limit))

    def get_result(self, result_id: str) -> dict:
        """
        Get details of a specific analytics result.

        Parameters:
            result_id: The ID of the analytics result.

        Returns:
            Description of the analytics result.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            result = pl.analytics.get_result("my-result-id")
            print(f"Result timestamp: {result['timestamp']}")
            ```
        """
        return self._client._call_sync(self._client.get_result(result_id))

    def download_result(self, result_id: str, format: str = 'json') -> dict:
        """
        Download analytics result data.

        Parameters:
            result_id: The ID of the analytics result.
            format: The format to download the result in (json, geojson, csv).

        Returns:
            The result data in the requested format.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            data = pl.analytics.download_result("my-result-id", format="geojson")
            print(f"Downloaded {len(data['features'])} features")
            ```
        """
        return self._client._call_sync(
            self._client.download_result(result_id, format))

    def get_feed_stats(
            self,
            feed_id: str,
            subscription_id: Optional[str] = None,
            start_time: Optional[Union[str, datetime]] = None,
            end_time: Optional[Union[str, datetime]] = None) -> dict:
        """
        Get statistics for an analytics feed.

        Parameters:
            feed_id: The ID of the analytics feed.
            subscription_id: If provided, get stats for this specific subscription.
            start_time: Start time for temporal filtering (ISO 8601 string or datetime).
            end_time: End time for temporal filtering (ISO 8601 string or datetime).

        Returns:
            Statistics for the analytics feed.

        Raises:
            planet.exceptions.APIError: On API error.

        Example:
            ```python
            pl = Planet()
            stats = pl.analytics.get_feed_stats("my-feed-id")
            print(f"Total results: {stats['total_results']}")
            ```
        """
        return self._client._call_sync(
            self._client.get_feed_stats(feed_id=feed_id,
                                        subscription_id=subscription_id,
                                        start_time=start_time,
                                        end_time=end_time))
