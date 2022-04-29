# Copyright 2022 Planet Labs, PBC.
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
"""Functionality for interacting with the data api"""
import logging
import typing

from .. import exceptions
from ..constants import PLANET_BASE_URL
from ..http import Session
from ..models import Paged, Request, Response

BASE_URL = f'{PLANET_BASE_URL}/data/v1/'
SEARCHES_PATH = '/searches'
STATS_PATH = '/stats'

STATS_INTERVAL = ('hour', 'day', 'week', 'month', 'year')

LOGGER = logging.getLogger(__name__)


class Items(Paged):
    '''Asynchronous iterator over items from a paged response.'''
    LINKS_KEY = '_links'
    NEXT_KEY = '_next'
    ITEMS_KEY = 'features'


class DataClient():
    """High-level asynchronous access to Planet's data API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session, DataClient
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = DataClient(sess)
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```
    """

    def __init__(self, session: Session, base_url: str = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production data API
                base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def _searches_url(self):
        return f'{self._base_url}{SEARCHES_PATH}'

    def _stats_url(self):
        return f'{self._base_url}{STATS_PATH}'

    def _request(self, url, method, data=None, params=None, json=None):
        return Request(url, method=method, data=data, params=params, json=json)

    async def _do_request(self, request: Request) -> Response:
        '''Submit a request and get response.

        Parameters:
            request: request to submit
        '''
        return await self._session.request(request)

    async def quick_search(self,
                           item_types: typing.List[str],
                           search_filter: dict,
                           name: str = None,
                           sort: str = None,
                           limit: int = None) -> typing.AsyncIterator[dict]:
        '''Execute a quick search.

        Quick searches are saved for a short period of time (~month). The
        `name` parameter of the search defaults to the search id if `name`
        is not given.

        Returns an iterator over all items matching the search.

        Example:

        ```python
        >>> import asyncio
        >>> from planet import Session, DataClient
        >>>
        >>> async def main():
        ...     item_types = ['PSScene']
        ...     sfilter = {
        ...         "type":"DateRangeFilter",
        ...         "field_name":"acquired",
        ...         "config":{
        ...             "gt":"2019-12-31T00:00:00Z",
        ...             "lte":"2020-01-31T00:00:00Z"
        ...         }
        ...     }
        ...     async with Session() as sess:
        ...         cl = DataClient(sess)
        ...         items = await cl.quick_search(item_types, sfilter)
        ...
        >>> asyncio.run(main())

        ```

        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            sort: Override default of 'published desc' for field and direction
                to order results by. Specified as '<field> <direction>' where
                direction is either 'desc' for descending direction or 'asc'
                for ascending direction.
            name: The name of the saved search.
            limit: Maximum number of items to return.

        Returns:
            Ordered items matching the filter.

        Raises:
            planet.exceptions.APIError: On API error.
        '''
        url = f'{self._base_url}/quick-search'

        # TODO: validate item_types
        request_json = {'filter': search_filter, 'item_types': item_types}
        if name:
            request_json['name'] = name

        params = {}
        if sort:
            # TODO: validate sort
            params['sort'] = sort

        request = self._request(url,
                                method='POST',
                                json=request_json,
                                params=params)
        return Items(request, self._do_request, limit=limit)

    async def create_search(self,
                            name: str,
                            item_types: typing.List[str],
                            search_filter: dict,
                            enable_email: bool = False) -> dict:
        '''Create a new saved structured item search.

        Parameters:
            name: The name of the saved search.
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            enable_email: Send a daily email when new results are added.

        Returns:
            Description of the saved search.

        Raises:
            planet.exceptions.APIError: On API error.
        '''
        url = self._searches_url()

        # TODO: validate item_types
        request_json = {
            'name': name, 'filter': search_filter, 'item_types': item_types
        }
        if enable_email:
            request_json['__daily_email_enabled'] = True

        request = self._request(url,
                                method='POST',
                                json=request_json)
        response = await self._do_request(request)
        return response.json()

    async def get_stats(self,
                        item_types: typing.List[str],
                        search_filter: dict,
                        interval: str) -> dict:
        '''Get item search statistics.

        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            interval: The size of the histogram date buckets.

        Returns:
            Returns a date bucketed histogram of items matching the filter.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If interval is not valid.
        '''
        if interval not in STATS_INTERVAL:
            raise exceptions.ClientError(
                f'{interval} must be one of {STATS_INTERVAL}')

        url = self._stats_url()
        request_json = {
            'interval': interval,
            'filter': search_filter,
            'item_types': item_types
        }
        request = self._request(url, method='POST', json=request_json)
        response = await self._do_request(request)
        return response.json()
