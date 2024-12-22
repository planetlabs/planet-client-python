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
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from ..http import Session

from planet.clients import DataClient

LIST_SORT_DEFAULT = 'created desc'
LIST_SEARCH_TYPE_DEFAULT = 'any'

WAIT_DELAY = 5
WAIT_MAX_ATTEMPTS = 200


class DataAPI:
    """Data API client"""

    _client: DataClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production data API
                base url.
        """
        self._client = DataClient(session, base_url)

    def search(
        self,
        item_types: List[str],
        search_filter: Optional[Dict] = None,
        name: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 100,
        geometry: Optional[Dict] = None,
    ) -> Iterator[Dict]:
        """
        Search for items

        Example:

        ```python
        pl = Planet()
        for item in pl.data.search(['PSScene'], limit=5):
            print(item)
        ```

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
        """

        results = self._client.search(item_types,
                                      search_filter,
                                      name,
                                      sort,
                                      limit,
                                      geometry)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass

    def create_search(
        self,
        item_types: List[str],
        search_filter: Dict,
        name: str,
        enable_email: bool = False,
        geometry: Optional[Dict] = None,
    ) -> Dict:
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
        return self._client._call_sync(
            self._client.create_search(item_types,
                                       search_filter,
                                       name,
                                       enable_email,
                                       geometry))

    def update_search(self,
                      search_id: str,
                      item_types: List[str],
                      search_filter: Dict[str, Any],
                      name: str,
                      enable_email: bool = False,
                      geometry: Optional[dict] = None) -> Dict[str, Any]:
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
        return self._client._call_sync(
            self._client.update_search(search_id,
                                       item_types,
                                       search_filter,
                                       name,
                                       enable_email,
                                       geometry))

    def list_searches(self,
                      sort: str = LIST_SORT_DEFAULT,
                      search_type: str = LIST_SEARCH_TYPE_DEFAULT,
                      limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Iterate through list of searches available to the user.

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
        results = self._client.list_searches(sort, search_type, limit)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass

    def delete_search(self, search_id: str):
        """Delete an existing saved search.

        Parameters:
            search_id: Saved search identifier.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.delete_search(search_id))

    def get_search(self, search_id: str) -> Dict:
        """Get a saved search by id.

        Parameters:
            search_id: Stored search identifier.

        Returns:
            Saved search details.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.get_search(search_id))

    def run_search(self,
                   search_id: str,
                   sort: Optional[str] = None,
                   limit: int = 100) -> Iterator[Dict[str, Any]]:
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

        results = self._client.run_search(search_id, sort, limit)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass

    def get_stats(self,
                  item_types: List[str],
                  search_filter: Dict[str, Any],
                  interval: str) -> Dict[str, Any]:
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
        return self._client._call_sync(
            self._client.get_stats(item_types, search_filter, interval))

    def list_item_assets(self, item_type_id: str,
                         item_id: str) -> Dict[str, Any]:
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
        return self._client._call_sync(
            self._client.list_item_assets(item_type_id, item_id))

    def get_asset(self, item_type_id: str, item_id: str,
                  asset_type_id: str) -> Dict[str, Any]:
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
        return self._client._call_sync(
            self._client.get_asset(item_type_id, item_id, asset_type_id))

    def activate_asset(self, asset: Dict[str, Any]):
        """Activate an item asset.

        Parameters:
            asset: Description of the asset. Obtained from get_asset().

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If asset description is not
            valid.
        """
        return self._client._call_sync(self._client.activate_asset(asset))

    def wait_asset(
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
        return self._client._call_sync(
            self._client.wait_asset(asset, delay, max_attempts, callback))

    def download_asset(self,
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
        return self._client._call_sync(
            self._client.download_asset(asset,
                                        filename,
                                        directory,
                                        overwrite,
                                        progress_bar))

    @staticmethod
    def validate_checksum(asset: Dict[str, Any], filename: Path):
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
        return DataClient.validate_checksum(asset, filename)
