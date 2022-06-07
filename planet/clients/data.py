# Copyright 2022 Planet Labs PBC.
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

LIST_SORT_ORDER = ('created desc', 'created asc')
LIST_SEARCH_TYPE = ('any', 'saved', 'quick')
STATS_INTERVAL = ('hour', 'day', 'week', 'month', 'year')

WAIT_DELAY = 5
WAIT_MAX_ATTEMPTS = 200

LOGGER = logging.getLogger(__name__)


class Items(Paged):
    """Asynchronous iterator over items from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'features'


class Searches(Paged):
    """Asynchronous iterator over searches from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'searches'


class DataClient:
    """Low-level asynchronous access to Planet's data API.

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

    def _request(self, url, method, data=None, params=None, json=None):
        return Request(url, method=method, data=data, params=params, json=json)

    async def _do_request(self, request: Request) -> Response:
        """Submit a request and get response.

        Parameters:
            request: request to submit
        """
        return await self._session.request(request)

    async def quick_search(
            self,
            item_types: typing.List[str],
            search_filter: dict,
            name: str = None,
            sort: str = None,
            limit: typing.Union[int,
                                None] = 100) -> typing.AsyncIterator[dict]:
        """Execute a quick search.

        Quick searches are saved for a short period of time (~month). The
        `name` parameter of the search defaults to the search id if `name`
        is not given.

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
            Returns an iterator over all items matching the search.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/quick-search'

        # Set no limit
        if limit == 0:
            limit = None

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
        """Create a new saved structured item search.

        Parameters:
            name: The name of the saved search.
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            enable_email: Send a daily email when new results are added.

        Returns:
            Description of the saved search.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._searches_url()

        # TODO: validate item_types
        request_json = {
            'name': name,
            'filter': search_filter,
            'item_types': item_types,
            '__daily_email_enabled': enable_email
        }

        request = self._request(url, method='POST', json=request_json)
        response = await self._do_request(request)
        return response.json()

    async def update_search(self,
                            search_id: str,
                            name: str,
                            item_types: typing.List[str],
                            search_filter: dict,
                            enable_email: bool = False) -> dict:
        """Update an existing saved search.

        Parameters:
            search_id: Saved search identifier.
            name: The name of the saved search.
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            enable_email: Send a daily email when new results are added.

        Returns:
            Description of the saved search.
        """
        url = f'{self._searches_url()}/{search_id}'

        request_json = {
            'name': name,
            'filter': search_filter,
            'item_types': item_types,
            '__daily_email_enabled': enable_email
        }

        request = self._request(url, method='PUT', json=request_json)
        response = await self._do_request(request)
        return response.json()

    async def list_searches(
            self,
            sort: str = 'created desc',
            search_type: str = 'any',
            limit: typing.Union[int,
                                None] = 100) -> typing.AsyncIterator[dict]:
        """List all saved searches available to the authenticated user.

        NOTE: the term 'saved' is overloaded here. We want to list saved
        searches that are 'quick' or list saved searches that are 'saved'? Do
        we want to introduce a new term, 'stored' that encompasses 'saved' and
        'quick' searches?

        Parameters:
            sort: Field and direction to order results by.
            search_type: Search type filter.
            limit: Maximum number of items to return.

        Returns:
            An iterator over all searches that match filter.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If sort or search_type are not
                valid.
        """
        sort = sort.lower()
        if sort not in LIST_SORT_ORDER:
            raise exceptions.ClientError(
                f'{sort} must be one of {LIST_SORT_ORDER}')

        search_type = search_type.lower()
        if search_type not in LIST_SEARCH_TYPE:
            raise exceptions.ClientError(
                f'{search_type} must be one of {LIST_SEARCH_TYPE}')

        url = f'{self._searches_url()}'
        request = self._request(url, method='GET')
        return Searches(request, self._do_request, limit=limit)

    async def delete_search(self, search_id: str):
        """Delete an existing saved search.

        Parameters:
            search_id: Saved search identifier.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._searches_url()}/{search_id}'

        request = self._request(url, method='DELETE')
        await self._do_request(request)

    async def get_search(self, search_id: str) -> dict:
        """Get a saved search by id.

        Parameters:
            search_id: Stored search identifier.

        Returns:
            Saved search details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def run_search(
            self,
            search_id: str,
            limit: typing.Union[int,
                                None] = 100) -> typing.AsyncIterator[dict]:
        """Execute a saved search.

        Parameters:
            search_id: Stored search identifier.
            limit: Maximum number of items to return.

        Returns:
            Returns an iterator over all items matching the search.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._searches_url()}/{search_id}/results'

        request = self._request(url, method='GET')
        return Items(request, self._do_request, limit=limit)

    async def get_stats(self,
                        item_types: typing.List[str],
                        search_filter: dict,
                        interval: str) -> dict:
        """Get item search statistics.

        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            interval: The size of the histogram date buckets.

        Returns:
            Returns a date bucketed histogram of items matching the filter.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If interval is not valid.
        """
        interval = interval.lower()
        if interval not in STATS_INTERVAL:
            raise exceptions.ClientError(
                f'{interval} must be one of {STATS_INTERVAL}')

        url = f'{self._base_url}{STATS_PATH}'
        request_json = {
            'interval': interval,
            'filter': search_filter,
            'item_types': item_types
        }
        request = self._request(url, method='POST', json=request_json)
        response = await self._do_request(request)
        return response.json()

    async def list_asset_types(self) -> typing.List[dict]:
        """List all asset types available to the authenticated user.

        Returns:
            List of asset type details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def get_asset_type(self, asset_type_id: str) -> dict:
        """Get an asset type by id.

        An asset describes a product that can be derived from an item's source
        data, and can be used for various analytic, visual or other purposes.
        These are referred to as asset_types.

        Parameters:
            asset_type_id: Asset type identifier.

        Returns:
            Asset type details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def list_item_types(self) -> typing.List[dict]:
        """List all item types available to the authenticated user.

        Returns:
            List of item type details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def get_item_type(self, item_type_id: str) -> dict:
        """Get an item type by id.

        An item_type represents the class of spacecraft and/or processing level
        of an item. All items have an associated item_type. Each item_type has
        a set of supported asset_types which may be produced for a given item.

        Parameters:
            item_type_id: Item type identifier.

        Returns:
            Item type details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def get_item(
        self,
        item_type_id: str,
        item_id: str,
    ) -> dict:
        """Get an item by id and item type id.

        In the Planet API, an item is an entry in our catalog, and generally
        represents a single logical observation (or scene) captured by a
        satellite. Each item is defined by an item_type_id, which specifies the
        class of spacecraft and/or processing level of the item. Assets (or
        products, such as visual or analytic) can be derived from the item's
        source data.

        Parameters:
            item_type_id: Item type identifier.

        Returns:
            Item details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def list_item_assets(self, item_type_id: str,
                               item_id: str) -> typing.List[dict]:
        """List all assets available for an item.

        An asset describes a product that can be derived from an item's source
        data, and can be used for various analytic, visual or other purposes.
        These are referred to as asset_types.

        Parameters:
            item_type_id: Item type identifier.
            item_id: Item identifier.

        Returns:
            Descriptions of available assets as a dictionary with asset_type_id
            as keys and asset description as value.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        raise NotImplementedError

    async def get_asset(self,
                        item_type_id: str,
                        item_id: str,
                        asset_type_id: str) -> dict:
        """Get an item asset.

        Parameters:
            item_type_id: Item type identifier.
            item_id: Item identifier.
            asset_type_id: Asset type identifier.

        Returns:
            Description of the asset.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset type identifier is not
            valid.
        """
        # NOTE: this is not an API endpoint
        # this is getting an asset by name from the dict returned by
        # list_item_assets()
        raise NotImplementedError

    async def activate_asset(self, asset: dict):
        """Activate an item asset.

        Parameters:
            asset: Description of the asset.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset description is not
            valid.
        """
        # NOTE: this is not an API endpoint
        # This is getting the 'activate' link from the asset description
        # and then sending the activate request to that link
        raise NotImplementedError

    async def wait_asset(self,
                         asset: dict,
                         delay: int = WAIT_DELAY,
                         max_attempts: int = WAIT_MAX_ATTEMPTS,
                         callback: typing.Callable[[str], None] = None) -> str:
        """Wait for an item asset to be active.

        Parameters:
            asset: Description of the asset.
            delay: Time (in seconds) between polls.
            max_attempts: Maximum number of polls. Set to zero for no limit.
            callback: Function that handles state progress updates.

        Returns:
            Last received description of the asset.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset_type_id is not valid or is
                not available or if the maximum number of attempts is reached
                before the asset is active.
        """
        # NOTE: this is not an API endpoint
        # This is getting and checking the asset status and waiting until
        # the asset is active
        # NOTE: use the url at asset['_links']['_self'] to get the current
        # asset status
        raise NotImplementedError

    async def download_asset(self,
                             asset: dict,
                             filename: str = None,
                             directory: str = None,
                             overwrite: bool = False,
                             progress_bar: bool = True) -> str:
        """Download an asset.

        Asset description is obtained from get_asset() or wait_asset().

        Parameters:
            asset: Description of the asset.
            location: Download location url including download token.
            filename: Custom name to assign to downloaded file.
            directory: Base directory for file download.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.

        Returns:
            Path to downloaded file.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset is not activated or asset
            description is not valid.
        """
        # NOTE: this is not an API endpoint
        # This is getting the download location from the asset description
        # and then downloading the file at that location
        raise NotImplementedError
