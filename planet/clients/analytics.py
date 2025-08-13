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

import logging
from typing import AsyncIterator, List, Optional, Union, TypeVar
from datetime import datetime

from planet.clients.base import _BaseClient
from planet.exceptions import ClientError
from planet.http import Session
from planet.models import Paged
from planet.constants import PLANET_BASE_URL

T = TypeVar("T")

BASE_URL = f'{PLANET_BASE_URL}/analytics/v1'

LOGGER = logging.getLogger(__name__)


class AnalyticsFeed(Paged):
    """Asynchronous iterator over analytics feeds from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'feeds'


class AnalyticsSubscription(Paged):
    """Asynchronous iterator over analytics subscriptions from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'subscriptions'


class AnalyticsResult(Paged):
    """Asynchronous iterator over analytics results from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'results'


class AnalyticsClient(_BaseClient):
    """Asynchronous Analytics API client

    The Analytics API provides programmatic access to Planet Analytic Feeds
    that detect and classify objects, identify geographic features, and
    understand change over time across the globe.

    For more information about the Analytics API, see the documentation at
    https://docs.planet.com/develop/apis/analytics/

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('analytics')
        ...         # use client here
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to the Analytics
                API base url at api.planet.com.
        """
        super().__init__(session, base_url or BASE_URL)

    async def list_feeds(self, limit: int = 0) -> AsyncIterator[dict]:
        """
        List available analytics feeds.

        Parameters:
            limit: Maximum number of feeds to return. When set to 0, no
                maximum is applied.

        Yields:
            Description of an analytics feed.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/feeds'

        response = await self._session.request(method='GET', url=url)
        async for feed in AnalyticsFeed(response,
                                        self._session.request,
                                        limit=limit):
            yield feed

    async def get_feed(self, feed_id: str) -> dict:
        """
        Get details of a specific analytics feed.

        Parameters:
            feed_id: The ID of the analytics feed.

        Returns:
            Description of the analytics feed.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/feeds/{feed_id}'
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def list_subscriptions(self,
                                 feed_id: Optional[str] = None,
                                 limit: int = 0) -> AsyncIterator[dict]:
        """
        List analytics subscriptions.

        Parameters:
            feed_id: If provided, only list subscriptions for this feed.
            limit: Maximum number of subscriptions to return. When set to 0, no
                maximum is applied.

        Yields:
            Description of an analytics subscription.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/subscriptions'
        params = {}
        if feed_id:
            params['feed_id'] = feed_id

        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for subscription in AnalyticsSubscription(response,
                                                        self._session.request,
                                                        limit=limit):
            yield subscription

    async def get_subscription(self, subscription_id: str) -> dict:
        """
        Get details of a specific analytics subscription.

        Parameters:
            subscription_id: The ID of the analytics subscription.

        Returns:
            Description of the analytics subscription.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/subscriptions/{subscription_id}'
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def search_results(self,
                             feed_id: str,
                             subscription_id: Optional[str] = None,
                             geometry: Optional[dict] = None,
                             start_time: Optional[Union[str, datetime]] = None,
                             end_time: Optional[Union[str, datetime]] = None,
                             bbox: Optional[List[float]] = None,
                             limit: int = 0) -> AsyncIterator[dict]:
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

        Yields:
            Analytics result.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/results/search'

        # Build search parameters
        params = {'feed_id': feed_id}

        if subscription_id:
            params['subscription_id'] = subscription_id

        if start_time:
            if isinstance(start_time, datetime):
                params['start_time'] = start_time.isoformat()
            else:
                params['start_time'] = start_time

        if end_time:
            if isinstance(end_time, datetime):
                params['end_time'] = end_time.isoformat()
            else:
                params['end_time'] = end_time

        if bbox:
            if len(bbox) != 4:
                raise ClientError(
                    "bbox must contain exactly 4 values: [west, south, east, north]"
                )
            params['bbox'] = ','.join(map(str, bbox))

        # Handle geometry in request body if provided
        json_data = None
        if geometry:
            json_data = {'geometry': geometry}

        method = 'POST' if json_data else 'GET'
        response = await self._session.request(method=method,
                                               url=url,
                                               params=params,
                                               json=json_data)

        async for result in AnalyticsResult(response,
                                            self._session.request,
                                            limit=limit):
            yield result

    async def get_result(self, result_id: str) -> dict:
        """
        Get details of a specific analytics result.

        Parameters:
            result_id: The ID of the analytics result.

        Returns:
            Description of the analytics result.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/results/{result_id}'
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def download_result(self,
                              result_id: str,
                              format: str = 'json') -> dict:
        """
        Download analytics result data.

        Parameters:
            result_id: The ID of the analytics result.
            format: The format to download the result in (json, geojson, csv).

        Returns:
            The result data in the requested format.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/results/{result_id}/download'
        params = {'format': format}

        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)

        if format.lower() == 'json' or format.lower() == 'geojson':
            return response.json()
        else:
            return response.text()

    async def get_feed_stats(
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
        """
        url = f'{self._base_url}/feeds/{feed_id}/stats'

        params = {}
        if subscription_id:
            params['subscription_id'] = subscription_id

        if start_time:
            if isinstance(start_time, datetime):
                params['start_time'] = start_time.isoformat()
            else:
                params['start_time'] = start_time

        if end_time:
            if isinstance(end_time, datetime):
                params['end_time'] = end_time.isoformat()
            else:
                params['end_time'] = end_time

        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        return response.json()
