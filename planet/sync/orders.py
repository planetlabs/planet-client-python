# Copyright 2020 Planet Labs, Inc.
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
"""Functionality for interacting with the orders api"""
from typing import Any, Callable, Dict, Iterator, List, Optional

from pathlib import Path
from ..http import Session
from planet.clients import OrdersClient


class OrdersAPI:
    """Orders API client"""

    _client: OrdersClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production orders API
                base url.
        """

        self._client = OrdersClient(session, base_url)

    def create_order(self, request: Dict) -> Dict:
        """Create an order.

        Example:

        ```python

        from planet import Planet, order_request

        def main():
             pl = Planet()
             image_ids = ["20200925_161029_69_2223"]
             request = order_request.build_request(
                 'test_order',
                 [order_request.product(image_ids, 'analytic_udm2', 'psscene')]
             )
             order = pl.orders.create_order(request)
        ```

        Parameters:
            request: order request definition (recommended to use the order_request module to build a request)

        Returns:
            JSON description of the created order

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.create_order(request))

    def get_order(self, order_id: str) -> Dict:
        """Get order details by Order ID.

        Parameters:
            order_id: The ID of the order

        Returns:
            JSON description of the order

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.get_order(order_id))

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a queued order.

        Parameters:
            order_id: The ID of the order

        Returns:
            Results of the cancel request

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.cancel_order(order_id))

    def cancel_orders(self,
                      order_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Cancel queued orders in bulk.

        Parameters:
            order_ids: The IDs of the orders. If empty or None, all orders in a
                pre-running state will be cancelled.

        Returns:
            Results of the bulk cancel request

        Raises:
            planet.exceptions.ClientError: If an entry in order_ids is not a
                valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.cancel_orders(order_ids))

    def aggregated_order_stats(self) -> Dict[str, Any]:
        """Get aggregated counts of active orders.

        Returns:
            Aggregated order counts

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.aggregated_order_stats())

    def download_asset(self,
                       location: str,
                       filename: Optional[str] = None,
                       directory: Path = Path('.'),
                       overwrite: bool = False,
                       progress_bar: bool = True) -> Path:
        """Download ordered asset.

        Parameters:
            location: Download location url including download token.
            filename: Custom name to assign to downloaded file.
            directory: Base directory for file download. This directory will be
                created if it does not already exist.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.

        Returns:
            Path to downloaded file.

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(
            self._client.download_asset(location,
                                        filename,
                                        directory,
                                        overwrite,
                                        progress_bar))

    def download_order(self,
                       order_id: str,
                       directory: Path = Path('.'),
                       overwrite: bool = False,
                       progress_bar: bool = False) -> List[Path]:
        """Download all assets in an order.

        Parameters:
            order_id: The ID of the order.
            directory: Base directory for file download. This directory must
                already exist.
            overwrite: Overwrite files if they already exist.
            progress_bar: Show progress bar during download.

        Returns:
            Paths to downloaded files.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If the order is not in a final
                state.
        """
        return self._client._call_sync(
            self._client.download_order(order_id,
                                        directory,
                                        overwrite,
                                        progress_bar))

    def validate_checksum(self, directory: Path, checksum: str):
        """Validate checksums of downloaded files against order manifest.

        For each file entry in the order manifest, the specified checksum given
        in the manifest file will be validated against the checksum calculated
        from the downloaded file.

        Parameters:
            directory: Path to order directory.
            checksum: The type of checksum hash- 'MD5' or 'SHA256'.

        Raises:
            planet.exceptions.ClientError: If a file is missing or if checksums
                do not match.
        """
        return self._client.validate_checksum(directory, checksum)

    def wait(self,
             order_id: str,
             state: Optional[str] = None,
             delay: int = 5,
             max_attempts: int = 200,
             callback: Optional[Callable[[str], None]] = None) -> str:
        """Wait until order reaches desired state.

        Returns the state of the order on the last poll.

        This function polls the Orders API to determine the order state, with
        the specified delay between each polling attempt, until the
        order reaches a final state, or earlier state, if specified.
        If the maximum number of attempts is reached before polling is
        complete, an exception is raised. Setting 'max_attempts' to zero will
        result in no limit on the number of attempts.

        Setting 'delay' to zero results in no delay between polling attempts.
        This will likely result in throttling by the Orders API, which has
        a rate limit of 10 requests per second. If many orders are being
        polled asynchronously, consider increasing the delay to avoid
        throttling.

        By default, polling completes when the order reaches a final state.
        If 'state' is given, polling will complete when the specified earlier
        state is reached or passed.

        Example:
            ```python
            from planet.reporting import StateBar

            with StateBar() as bar:
                wait(order_id, callback=bar.update_state)
            ```

        Parameters:
            order_id: The ID of the order.
            state: State prior to a final state that will end polling.
            delay: Time (in seconds) between polls.
            max_attempts: Maximum number of polls. Set to zero for no limit.
            callback: Function that handles state progress updates.

        Returns
            State of the order.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If order_id or state is not valid or
                if the maximum number of attempts is reached before the
                specified state or a final state is reached.
        """
        return self._client._call_sync(
            self._client.wait(order_id, state, delay, max_attempts, callback))

    def list_orders(self,
                    state: Optional[str] = None,
                    limit: int = 100,
                    source_type: Optional[str] = None,
                    name: Optional[str] = None,
                    name__contains: Optional[str] = None,
                    created_on: Optional[str] = None,
                    last_modified: Optional[str] = None,
                    hosting: Optional[bool] = None,
                    sort_by: Optional[str] = None) -> Iterator[dict]:
        """Iterate over the list of stored orders.

        By default, order descriptions are sorted by creation date with the last created
        order returned first.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Parameters:
            state (str): filter by state.
            source_type (str): filter by source type.
            name (str): filter by name.
            name__contains (str): only include orders with names containing this string.
            created_on (str): filter by creation date-time or interval.
            last_modified (str): filter by last modified date-time or interval.
            hosting (bool): only return orders that contain a hosting block
                (e.g. SentinelHub hosting).
            sort_by (str): fields to sort orders by. Multiple fields can be specified,
                separated by commas. The sort direction can be specified by appending
                ' ASC' or ' DESC' to the field name. The default sort direction is
                ascending. When multiple fields are specified, the sort order is applied
                in the order the fields are listed.

                Supported fields: name, created_on, state, last_modified

                Examples:
                 * "name"
                 * "name DESC"
                 * "name,state DESC,last_modified"
            limit (int): maximum number of results to return. When set to 0, no
                maximum is applied.

        Datetime args (created_on and last_modified) can either be a date-time or an
        interval, open or closed. Date and time expressions adhere to RFC 3339. Open
        intervals are expressed using double-dots.

        Yields:
            Description of an order.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If state is not valid.
        """
        results = self._client.list_orders(state,
                                           limit,
                                           source_type,
                                           name,
                                           name__contains,
                                           created_on,
                                           last_modified,
                                           hosting,
                                           sort_by)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass
