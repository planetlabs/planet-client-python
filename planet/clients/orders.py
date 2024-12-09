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
import asyncio
import logging
import time
from typing import AsyncIterator, Callable, List, Optional, Sequence, Union, Dict
import uuid
import json
import hashlib

from pathlib import Path
from .. import exceptions
from ..constants import PLANET_BASE_URL
from ..http import Session
from ..models import Paged, StreamingBody

BASE_URL = f'{PLANET_BASE_URL}/compute/ops'
STATS_PATH = '/stats/orders/v2'
ORDERS_PATH = '/orders/v2'
BULK_PATH = '/bulk/orders/v2'

# Order states https://developers.planet.com/docs/orders/ordering/#order-states
# this is in order of state progression except for final states
ORDER_STATE_SEQUENCE = \
    ('queued', 'running', 'failed', 'success', 'partial', 'cancelled')

LOGGER = logging.getLogger(__name__)


class Orders(Paged):
    """Asynchronous iterator over Orders from a paged response describing
    orders."""
    ITEMS_KEY = 'orders'


class OrderStates:
    SEQUENCE = ORDER_STATE_SEQUENCE

    @classmethod
    def _get_position(cls, state):
        return cls.SEQUENCE.index(state)

    @classmethod
    def reached(cls, state, test):
        return cls._get_position(test) >= cls._get_position(state)

    @classmethod
    def passed(cls, state, test):
        return cls._get_position(test) > cls._get_position(state)

    @classmethod
    def is_final(cls, test):
        return cls.passed('running', test)


class OrdersClient:
    """High-level asynchronous access to Planet's orders API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('orders')
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```
    """

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production orders API
                base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    @staticmethod
    def _check_order_id(oid):
        """Raises planet.exceptions.ClientError if oid is not a valid UUID"""
        try:
            uuid.UUID(hex=oid)
        except (ValueError, AttributeError):
            msg = f'Order id ({oid}) is not a valid UUID hexadecimal string.'
            raise exceptions.ClientError(msg)

    def _orders_url(self):
        return f'{self._base_url}{ORDERS_PATH}'

    def _stats_url(self):
        return f'{self._base_url}{STATS_PATH}'

    async def create_order(self, request: dict) -> dict:
        """Create an order request.

        Example:

        ```python
        >>> import asyncio
        >>> from planet import Session
        >>> from planet.order_request import build_request, product
        >>>
        >>> async def main():
        ...     image_ids = ["20200925_161029_69_2223"]
        ...     request = build_request(
        ...         'test_order',
        ...         [product(image_ids, 'analytic_udm2', 'psscene')]
        ...     )
        ...     async with Session() as sess:
        ...         cl = sess.client('orders')
        ...         order = await cl.create_order(request)
        ...
        >>> asyncio.run(main())
        ```

        Parameters:
            request: order request definition

        Returns:
            JSON description of the created order

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._orders_url()
        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def get_order(self, order_id: str) -> dict:
        """Get order details by Order ID.

        Parameters:
            order_id: The ID of the order

        Returns:
            JSON description of the order

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)
        url = f'{self._orders_url()}/{order_id}'

        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel a queued order.

        Parameters:
            order_id: The ID of the order

        Returns:
            Results of the cancel request

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)
        url = f'{self._orders_url()}/{order_id}'

        response = await self._session.request(method='PUT', url=url)
        return response.json()

    async def cancel_orders(self,
                            order_ids: Optional[List[str]] = None) -> dict:
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
        url = f'{self._base_url}{BULK_PATH}/cancel'
        cancel_body = {}
        if order_ids:
            for oid in order_ids:
                self._check_order_id(oid)
            cancel_body['order_ids'] = order_ids

        response = await self._session.request(method='POST',
                                               url=url,
                                               json=cancel_body)

        return response.json()

    async def aggregated_order_stats(self) -> dict:
        """Get aggregated counts of active orders.

        Returns:
            Aggregated order counts

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._stats_url()
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def download_asset(self,
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
        async with self._session.stream(method='GET', url=location) as resp:
            body = StreamingBody(resp)
            dl_path = Path(directory, filename or body.name)
            dl_path.parent.mkdir(exist_ok=True, parents=True)
            await body.write(dl_path,
                             overwrite=overwrite,
                             progress_bar=progress_bar)
        return dl_path

    async def download_order(self,
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
        order = await self.get_order(order_id)
        order_state = order['state']
        if not OrderStates.is_final(order_state):
            raise exceptions.ClientError(
                'Order cannot be downloaded because the order state '
                f'({order_state}) is not a final state. '
                'Consider using wait functionality before '
                'attempting to download.')

        info = self._get_download_info(order)
        LOGGER.info(f'downloading {len(info)} assets from order {order_id}')

        filenames = [
            await self.download_asset(i['location'],
                                      filename=i['filename'],
                                      directory=directory / i['directory'],
                                      overwrite=overwrite,
                                      progress_bar=progress_bar) for i in info
        ]

        return filenames

    @staticmethod
    def _get_download_info(order):
        links = order['_links']
        results = links.get('results', [])

        def _info_from_result(result):
            name = Path(result['name'])
            return {
                'location': result['location'],
                'directory': name.parent,
                'filename': name.name
            }

        try:
            info = list(_info_from_result(r) for r in results if r)
        except TypeError:
            LOGGER.warning(
                'order does not have any locations, will not download any ' +
                'files.')
            info = []
        return info

    @staticmethod
    def validate_checksum(directory: Path, checksum: str):
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
        manifest_path = directory / 'manifest.json'

        try:
            manifest_data = json.loads(manifest_path.read_text())
        except FileNotFoundError:
            raise exceptions.ClientError(
                f'File ({manifest_path}) does not exist.')
        except json.decoder.JSONDecodeError:
            raise exceptions.ClientError(
                f'Manifest file ({manifest_path}) does not contain valid JSON.'
            )

        if checksum.upper() == 'MD5':
            hash_type = hashlib.md5
        elif checksum.upper() == 'SHA256':
            hash_type = hashlib.sha256
        else:
            raise exceptions.ClientError(
                f'Checksum ({checksum}) must be one of MD5 or SHA256.')

        for json_entry in manifest_data['files']:
            origin_hash = json_entry['digests'][checksum.lower()]

            filename = directory / json_entry['path']
            try:
                returned_hash = hash_type(filename.read_bytes()).hexdigest()
            except FileNotFoundError:
                raise exceptions.ClientError(
                    f'Checksum failed. File ({filename}) does not exist.')

            if origin_hash != returned_hash:
                raise exceptions.ClientError(
                    f'File ({filename}) checksums do not match.')

    async def wait(self,
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
                await wait(order_id, callback=bar.update_state)
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
        if state and state not in ORDER_STATE_SEQUENCE:
            raise exceptions.ClientError(
                f'{state} must be one of {ORDER_STATE_SEQUENCE}')

        # loop without end if max_attempts is zero
        # otherwise, loop until num_attempts reaches max_attempts
        num_attempts = 0
        while not max_attempts or num_attempts < max_attempts:
            t = time.time()

            order = await self.get_order(order_id)
            current_state = order['state']

            LOGGER.debug(current_state)

            if callback:
                callback(current_state)

            if OrderStates.is_final(current_state) or \
                    (state and OrderStates.reached(state, current_state)):
                break

            sleep_time = max(delay - (time.time() - t), 0)
            LOGGER.debug(f'sleeping {sleep_time}s')
            await asyncio.sleep(sleep_time)

            num_attempts += 1

        if max_attempts and num_attempts >= max_attempts:
            raise exceptions.ClientError(
                f'Maximum number of attempts ({max_attempts}) reached.')

        return current_state

    async def list_orders(
            self,
            state: Optional[str] = None,
            limit: int = 100,
            source_type: Optional[str] = None,
            name: Optional[str] = None,
            name__contains: Optional[str] = None,
            created_on: Optional[str] = None,
            last_modified: Optional[str] = None,
            hosting: Optional[bool] = None,
            sort_by: Optional[str] = None) -> AsyncIterator[dict]:
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

        Examples:
            * A date-time: "2018-02-12T23:20:50Z"
            * A closed interval: "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z"
            * Open intervals: "2018-02-12T00:00:00Z/.." or "../2018-03-18T12:31:12Z"

        Yields:
            Description of an order.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If state is not valid.
        """
        url = self._orders_url()
        params: Dict[str, Union[str, Sequence[str], bool]] = {}
        if source_type is not None:
            params["source_type"] = source_type
        else:
            params["source_type"] = "all"
        if name is not None:
            params["name"] = name
        if name__contains is not None:
            params["name__contains"] = name__contains
        if created_on is not None:
            params["created_on"] = created_on
        if last_modified is not None:
            params["last_modified"] = last_modified
        if hosting is not None:
            params["hosting"] = hosting
        if sort_by is not None:
            params["sort_by"] = sort_by
        if state:
            if state not in ORDER_STATE_SEQUENCE:
                raise exceptions.ClientError(
                    f'Order state ({state}) is not a valid state. '
                    f'Valid states are {ORDER_STATE_SEQUENCE}')
            params['state'] = state

        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for o in Orders(response, self._session.request, limit=limit):
            yield o
