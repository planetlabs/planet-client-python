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
import asyncio
import hashlib
import logging
from pathlib import Path
import time
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
import uuid

from ..data_filter import empty_filter
from .. import exceptions
from ..constants import PLANET_BASE_URL
from ..http import Session
from ..models import Paged, StreamingBody
from ..specs import validate_data_item_type
from ..geojson import as_geom_or_ref

BASE_URL = f'{PLANET_BASE_URL}/data/v1/'
SEARCHES_PATH = '/searches'
STATS_PATH = '/stats'

# TODO: get these values from the spec directly gh-619
# NOTE: these values are mached against a lower-case value so must also be
# lower-case
LIST_SORT_ORDER = ('created desc', 'created asc')
LIST_SEARCH_TYPE = ('any', 'saved', 'quick')
LIST_SORT_DEFAULT = 'created desc'
LIST_SEARCH_TYPE_DEFAULT = 'any'

SEARCH_SORT = ('published desc',
               'published asc',
               'acquired desc',
               'acquired asc')
SEARCH_SORT_DEFAULT = 'published desc'
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
    """High-level asynchronous access to Planet's data API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('data')
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```
    """

    def __init__(self, session: Session, base_url: Optional[str] = None):
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

    @staticmethod
    def _check_search_id(sid):
        """Raises planet.exceptions.ClientError if sid is not a valid UUID"""
        try:
            uuid.UUID(hex=sid)
        except (ValueError, AttributeError):
            msg = f'Search id ({sid}) is not a valid UUID hexadecimal string.'
            raise exceptions.ClientError(msg)

    def _searches_url(self):
        return f'{self._base_url}{SEARCHES_PATH}'

    def _item_url(self, item_type, item_id):
        return f'{self._base_url}/item-types/{item_type}/items/{item_id}'

    async def search(self,
                     item_types: List[str],
                     search_filter: Optional[dict] = None,
                     name: Optional[str] = None,
                     sort: Optional[str] = None,
                     limit: int = 100,
                     geometry: Optional[dict] = None) -> AsyncIterator[dict]:
        """Iterate over results from a quick search.

        Quick searches are saved for a short period of time (~month). The
        `name` parameter of the search defaults to the id of the generated
        search id if `name` is not specified.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria to apply. If None,
                no search criteria is applied.
            sort: Field and direction to order results by. Valid options are
            given in SEARCH_SORT.
            name: The name of the saved search.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.
            geometry: GeoJSON, a feature reference or a list of feature
                references

        Yields:
            Description of an item.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/quick-search'

        search_filter = search_filter or empty_filter()

        item_types = [validate_data_item_type(item) for item in item_types]
        request_json = {'filter': search_filter, 'item_types': item_types}

        if geometry:
            request_json['geometry'] = as_geom_or_ref(geometry)
        if name:
            request_json['name'] = name

        params = {}
        if sort and sort != SEARCH_SORT_DEFAULT:
            sort = sort.lower()
            if sort not in SEARCH_SORT:
                raise exceptions.ClientError(
                    f'{sort} must be one of {SEARCH_SORT}')
            params['_sort'] = sort
        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request_json,
                                               params=params)
        async for i in Items(response, self._session.request, limit=limit):
            yield i

    async def create_search(
        self,
        item_types: List[str],
        search_filter: dict,
        name: str,
        enable_email: bool = False,
        geometry: Optional[dict] = None,
    ) -> dict:
        """Create a new saved structured item search.

        To filter to items you have access to download which are of standard
        (aka not test) quality, use the following:

        ```python
        >>> from planet import data_filter
        >>> data_filter.and_filter([
        ...     data_filter.permission_filter(),
        ...     data_filter.std_quality_filter()
        >>> ])

        ```

        To avoid filtering out any imagery, supply a blank AndFilter, which can
        be created with `data_filter.and_filter([])`.


        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            name: The name of the saved search.
            enable_email: Send a daily email when new results are added.
            geometry: A feature reference or a GeoJSON

        Returns:
            Description of the saved search.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._searches_url()

        item_types = [validate_data_item_type(item) for item in item_types]

        request = {
            'name': name,
            'filter': search_filter,
            'item_types': item_types,
            '__daily_email_enabled': enable_email
        }
        if geometry:
            request['geometry'] = as_geom_or_ref(geometry)

        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def update_search(self,
                            search_id: str,
                            item_types: List[str],
                            search_filter: dict,
                            name: str,
                            enable_email: bool = False,
                            geometry: Optional[dict] = None) -> dict:
        """Update an existing saved search.

        Parameters:
            search_id: Saved search identifier.
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            name: The name of the saved search.
            enable_email: Send a daily email when new results are added.
            geometry: A feature reference or a GeoJSON

        Returns:
            Description of the saved search.
        """
        url = f'{self._searches_url()}/{search_id}'

        item_types = [validate_data_item_type(item) for item in item_types]

        request = {
            'name': name,
            'filter': search_filter,
            'item_types': item_types,
            '__daily_email_enabled': enable_email
        }
        if geometry:
            request['geometry'] = geometry

        response = await self._session.request(method='PUT',
                                               url=url,
                                               json=request)
        return response.json()

    async def list_searches(self,
                            sort: str = LIST_SORT_DEFAULT,
                            search_type: str = LIST_SEARCH_TYPE_DEFAULT,
                            limit: int = 100) -> AsyncIterator[dict]:
        """Iterate through list of searches available to the user.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Parameters:
            sort: Field and direction to order results by.
            search_type: Filter to specified search type.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.

        Yields:
            Description of a search.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If sort or search_type are not
                valid.
        """
        params = {}

        sort = sort.lower()
        if sort not in LIST_SORT_ORDER:
            raise exceptions.ClientError(
                f'{sort} must be one of {LIST_SORT_ORDER}')
        elif sort != LIST_SORT_DEFAULT:
            params['_sort'] = sort

        search_type = search_type.lower()
        if search_type not in LIST_SEARCH_TYPE:
            raise exceptions.ClientError(
                f'{search_type} must be one of {LIST_SEARCH_TYPE}')
        elif search_type != LIST_SEARCH_TYPE_DEFAULT:
            params['search_type'] = search_type

        url = self._searches_url()
        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for s in Searches(response, self._session.request, limit=limit):
            yield s

    async def delete_search(self, search_id: str):
        """Delete an existing saved search.

        Parameters:
            search_id: Saved search identifier.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._searches_url()}/{search_id}'

        await self._session.request(method='DELETE', url=url)

    async def get_search(self, search_id: str) -> dict:
        """Get a saved search by id.

        Parameters:
            search_id: Stored search identifier.

        Returns:
            Saved search details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._searches_url()}/{search_id}'

        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def run_search(self,
                         search_id: str,
                         sort: Optional[str] = None,
                         limit: int = 100) -> AsyncIterator[dict]:
        """Iterate over results from a saved search.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Parameters:
            search_id: Stored search identifier.
            sort: Field and direction to order results by. Valid options are
            given in SEARCH_SORT.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.

        Yields:
            Description of an item.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If search_id or sort is not valid.
        """
        self._check_search_id(search_id)
        url = f'{self._searches_url()}/{search_id}/results'

        params = {}
        if sort and sort != SEARCH_SORT_DEFAULT:
            sort = sort.lower()
            if sort not in SEARCH_SORT:
                raise exceptions.ClientError(
                    f'{sort} must be one of {SEARCH_SORT}')
            params['_sort'] = sort

        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for i in Items(response, self._session.request, limit=limit):
            yield i

    async def get_stats(self,
                        item_types: List[str],
                        search_filter: dict,
                        interval: str) -> dict:
        """Get item search statistics.

        Parameters:
            item_types: The item types to include in the search.
            search_filter: Structured search criteria.
            interval: The size of the histogram date buckets.

        Returns:
            A full JSON description of the returned statistics result
            histogram.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If interval is not valid.
        """
        interval = interval.lower()
        if interval not in STATS_INTERVAL:
            raise exceptions.ClientError(
                f'{interval} must be one of {STATS_INTERVAL}')

        url = f'{self._base_url}{STATS_PATH}'

        item_types = [validate_data_item_type(item) for item in item_types]
        request = {
            'interval': interval,
            'filter': search_filter,
            'item_types': item_types
        }

        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def list_item_assets(self, item_type_id: str, item_id: str) -> dict:
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
        url = f'{self._item_url(item_type_id, item_id)}/assets'

        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def get_asset(self,
                        item_type_id: str,
                        item_id: str,
                        asset_type_id: str) -> dict:
        """Get an item asset description.

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
        item_type_id = validate_data_item_type(item_type_id)
        assets = await self.list_item_assets(item_type_id, item_id)

        try:
            asset = assets[asset_type_id]
        except KeyError:
            valid = list(assets.keys())
            raise exceptions.ClientError(
                f'asset_type_id ({asset_type_id}) must be one of {valid}')

        return asset

    async def activate_asset(self, asset: dict):
        """Activate an item asset.

        Parameters:
            asset: Description of the asset. Obtained from get_asset().

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset description is not
            valid.
        """
        try:
            status = asset['status']
        except KeyError:
            raise exceptions.ClientError('asset missing ["status"] entry.')

        try:
            url = asset['_links']['activate']
        except KeyError:
            raise exceptions.ClientError(
                'asset missing ["_links"]["activate"] entry')

        # lets not try to activate an asset already activating or active
        if status == 'inactive':
            # no response is returned
            await self._session.request(method='GET', url=url)

        return

    async def wait_asset(
            self,
            asset: dict,
            delay: int = WAIT_DELAY,
            max_attempts: int = WAIT_MAX_ATTEMPTS,
            callback: Optional[Callable[[str],
                                        None]] = None) -> Dict[Any, Any]:
        """Wait for an item asset to be active.

        Prior to waiting for the asset to be active, be sure to activate the
        asset with activate_asset().

        Parameters:
            asset: Description of the asset. Obtained from get_asset().
            delay: Time (in seconds) between polls.
            max_attempts: Maximum number of polls. When set to 0, no limit
                is applied.
            callback: Function that handles state progress updates.

        Returns:
            Last received description of the asset.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset_type_id is not valid or is
                not available or if the maximum number of attempts is reached
                before the asset is active.
        """
        # loop without end if max_attempts is zero
        # otherwise, loop until num_attempts reaches max_attempts
        num_attempts = 0
        while not max_attempts or num_attempts < max_attempts:
            t = time.time()

            try:
                current_status = asset['status']
            except KeyError:
                raise exceptions.ClientError('asset missing ["status"] entry.')

            LOGGER.debug(current_status)

            if callback:
                callback(current_status)

            if current_status == 'active':
                break

            sleep_time = max(delay - (time.time() - t), 0)
            LOGGER.debug(f'sleeping {sleep_time}s')
            await asyncio.sleep(sleep_time)

            num_attempts += 1

            try:
                asset_url = asset['_links']['_self']
            except KeyError:
                raise exceptions.ClientError(
                    'asset missing ["_links"]["_self"] entry.')

            response = await self._session.request(method='GET', url=asset_url)
            asset = response.json()

        if max_attempts and num_attempts >= max_attempts:
            raise exceptions.ClientError(
                f'Maximum number of attempts ({max_attempts}) reached.')

        return asset

    async def download_asset(self,
                             asset: dict,
                             filename: Optional[str] = None,
                             directory: Path = Path('.'),
                             overwrite: bool = False,
                             progress_bar: bool = True) -> Path:
        """Download an asset.

        The asset must be active before it can be downloaded. This can be
        achieved with activate_asset() followed by wait_asset().

        If overwrite is False and the file already exists, download will be
        skipped and the file path will be returned as usual.

        Parameters:
            asset: Description of the asset. Obtained from get_asset() or
                wait_asset().
            filename: Custom name to assign to downloaded file.
            directory: Base directory for file download.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.

        Returns:
            Path to downloaded file.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset is not active or asset
            description is not valid.
        """
        try:
            location = asset['location']
        except KeyError:
            raise exceptions.ClientError(
                'asset missing ["location"] entry. Is asset active?')

        async with self._session.stream(method='GET', url=location) as resp:
            body = StreamingBody(resp)
            dl_path = Path(directory, filename or body.name)
            dl_path.parent.mkdir(exist_ok=True, parents=True)
            await body.write(dl_path,
                             overwrite=overwrite,
                             progress_bar=progress_bar)
        return dl_path

    @staticmethod
    def validate_checksum(asset: dict, filename: Path):
        """Validate checksum of downloaded file

        Compares checksum calculated from the file against the value provided
        in the asset.

        Parameters:
            asset: Description of the asset. Obtained from get_asset() or
                wait_asset().
            filename: Full path to downloaded file.

        Raises:
            planet.exceptions.ClientError: If the file does not exist or if
                checksums do not match.
        """
        try:
            file_hash = hashlib.md5(filename.read_bytes()).hexdigest()
        except FileNotFoundError:
            raise exceptions.ClientError(f'File ({filename}) does not exist.')

        try:
            origin_hash = asset['md5_digest']
        except KeyError:
            raise exceptions.ClientError(
                'asset missing ["md5_digest"] entry. Is asset active?')

        if origin_hash != file_hash:
            raise exceptions.ClientError(
                f'File ({filename}) checksums do not match.')
