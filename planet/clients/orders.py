# Copyright 2020 Planet Labs, Inc.
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
import json
import logging
import os
import time
import typing
import uuid

from .. import exceptions
from ..constants import PLANET_BASE_URL
from ..http import Session
from ..models import Order, Orders, Request, Response, StreamingBody

BASE_URL = f'{PLANET_BASE_URL}/compute/ops'
STATS_PATH = '/stats/orders/v2'
ORDERS_PATH = '/orders/v2'
BULK_PATH = '/bulk/orders/v2'

# Order states https://developers.planet.com/docs/orders/ordering/#order-states
ORDERS_STATES_COMPLETE = set(['success', 'partial', 'cancelled', 'failed'])
ORDERS_STATES_ALL = ORDERS_STATES_COMPLETE | set(['queued', 'running'])

LOGGER = logging.getLogger(__name__)


class OrdersClient():
    """High-level asynchronous access to Planet's orders API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session, OrdersClient
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = OrdersClient(sess)
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```
    """

    def __init__(self, session: Session, base_url: str = None):
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
        """Raises planet.exceptions.ValueError if oid is not a valid UUID"""
        try:
            uuid.UUID(hex=oid)
        except (ValueError, AttributeError):
            msg = f'Order id ({oid}) is not a valid UUID hexadecimal string.'
            raise exceptions.ValueError(msg)

    def _orders_url(self):
        return f'{self._base_url}{ORDERS_PATH}'

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

    async def create_order(self, request: dict) -> str:
        '''Create an order request.

        Example:

        ```python
        >>> import asyncio
        >>> from planet import Session, OrdersClient
        >>> from planet.order_request import build_request, product
        >>>
        >>> async def main():
        ...     image_ids = ['3949357_1454705_2020-12-01_241c']
        ...     request = build_request(
        ...         'test_order',
        ...         [product(image_ids, 'analytic', 'psorthotile')]
        ...     )
        ...     async with Session() as sess:
        ...         cl = OrdersClient(sess)
        ...         order_id = await cl.create_order(request)
        ...
        >>> asyncio.run(main())

        ```

        Parameters:
            request: order request definition

        Returns:
            The ID of the order

        Raises:
            planet.exceptions.APIException: On API error.
        '''
        url = self._orders_url()
        req = self._request(url, method='POST', json=request)

        try:
            resp = await self._do_request(req)
        except exceptions.BadQuery as ex:
            msg_json = json.loads(ex.message)

            msg = msg_json['general'][0]['message']
            try:
                # get first error field
                field = next(iter(msg_json['field'].keys()))
                msg += ' - ' + msg_json['field'][field][0]['message']
            except AttributeError:
                pass
            raise exceptions.BadQuery(msg)

        order = Order(resp.json())
        return order

    async def get_order(self, order_id: str) -> Order:
        '''Get order details by Order ID.

        Parameters:
            order_id: The ID of the order

        Returns:
            Order information

        Raises:
            planet.exceptions.ValueError: If order_id is not a valid UUID.
            planet.exceptions.APIException: On API error.
        '''
        self._check_order_id(order_id)
        url = f'{self._orders_url()}/{order_id}'

        req = self._request(url, method='GET')

        try:
            resp = await self._do_request(req)
        except exceptions.MissingResource as ex:
            msg_json = json.loads(ex.message)
            msg = msg_json['message']
            raise exceptions.MissingResource(msg)

        order = Order(resp.json())
        return order

    async def cancel_order(self, order_id: str) -> Response:
        '''Cancel a queued order.

        **Note:** According to the API docs, cancel order should return the
        cancelled order details. But testing reveals that an empty response is
        returned upon success.

        Parameters:
            order_id: The ID of the order

        Returns:
            Empty response

        Raises:
            planet.exceptions.ValueError: If order_id is not a valid UUID.
            planet.exceptions.APIException: On API error.
        '''
        self._check_order_id(order_id)
        url = f'{self._orders_url()}/{order_id}'

        req = self._request(url, method='PUT')

        try:
            await self._do_request(req)
        except exceptions.Conflict as ex:
            msg = json.loads(ex.message)['message']
            raise exceptions.Conflict(msg)
        except exceptions.MissingResource as ex:
            msg = json.loads(ex.message)['message']
            raise exceptions.MissingResource(msg)

    async def cancel_orders(self, order_ids: typing.List[str] = None) -> dict:
        '''Cancel queued orders in bulk.

        Parameters:
            order_ids: The IDs of the orders. If empty or None, all orders in a
                pre-running state will be cancelled.

        Returns:
            Results of the bulk cancel request

        Raises:
            planet.exceptions.ValueError: If an entry in order_ids is not a
                valid UUID.
            planet.exceptions.APIException: On API error.
        '''
        url = f'{self._base_url}{BULK_PATH}/cancel'
        cancel_body = {}
        if order_ids:
            for oid in order_ids:
                self._check_order_id(oid)
            cancel_body['order_ids'] = order_ids

        req = self._request(url, method='POST', json=cancel_body)
        resp = await self._do_request(req)
        return resp.json()

    async def aggregated_order_stats(self) -> dict:
        '''Get aggregated counts of active orders.

        Returns:
            Aggregated order counts

        Raises:
            planet.exceptions.APIException: On API error.
        '''
        url = self._stats_url()
        req = self._request(url, method='GET')
        resp = await self._do_request(req)
        return resp.json()

    async def download_asset(self,
                             location: str,
                             filename: str = None,
                             directory: str = None,
                             overwrite: bool = False,
                             progress_bar: bool = True) -> str:
        """Download ordered asset.

        Parameters:
            location: Download location url including download token.
            filename: Custom name to assign to downloaded file.
            directory: Write to given directory instead of current directory.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.

        Returns:
            Path to downloaded file.

        Raises:
            planet.exceptions.APIException: On API error.
        """
        req = self._request(location, method='GET')

        async with self._session.stream(req) as resp:
            body = StreamingBody(resp)
            dl_path = os.path.join(directory or '.', filename or body.name)
            await body.write(dl_path,
                             overwrite=overwrite,
                             progress_bar=progress_bar)
        return dl_path

    async def download_order(self,
                             order_id: str,
                             directory: str = None,
                             overwrite: bool = False,
                             progress_bar: bool = False) -> typing.List[str]:
        """Download all assets in an order.

        Parameters:
            order_id: The ID of the order
            directory: Write to given directory instead of current directory.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.

        Returns:
            Paths to downloaded files.

        Raises:
            planet.exceptions.APIException: On API error.
            planet.exceptions.StateError: If the order is not in a completed
                state.
        """
        order = await self.get_order(order_id)
        if order.state not in ORDERS_STATES_COMPLETE:
            raise exceptions.StateError(
                order.state,
                'Order cannot be downloaded because the order is not in a '
                'completed state. Consider using wait functionality before '
                'attempting to download.')

        locations = order.locations
        LOGGER.info(
            f'downloading {len(locations)} assets from order {order_id}')
        filenames = [
            await self.download_asset(location,
                                      directory=directory,
                                      overwrite=overwrite,
                                      progress_bar=progress_bar)
            for location in locations
        ]
        return filenames

    async def wait(
        self,
        order_id: str,
        states: typing.Iterable[str] = ORDERS_STATES_COMPLETE,
        delay: int = 5,
        max_attempts: int = 200,
        report: typing.Callable[[str], None] = None
    ) -> str:
        """Wait until order reaches one of the specified states.

        This function polls the Orders API to determine the order state, with
        the specified delay between each polling attempt, until the
        order reaches one of the set of desired states. If the maximum number
        of attempts is reached before the order reaches one of the desired
        states, an exception is raised. Setting 'max_attempts' to zero will
        result in no limit on the number of attempts.

        Setting 'delay' to zero results in no delay between polling attempts.
        This will likely result in throttling by the Orders API, which has
        a rate limit of 10 requests per second. If many orders are being
        polled asynchronously, consider increasing the delay to avoid
        throttling.

        By default, the set of states that result are polled for is the
        set of completed states. This can be changed to any set of valid
        order states. It is not recommended to change this to a subset of
        completed states, as this opens up the possibility of the the
        specified state never being reached (i.e. if the order completes in
        a 'partial' state but only the 'success' state was specified).

        Example:
            ```python
            from planet.reporting import StateBar

            with StateBar() as bar:
                await wait(order_id, report=bar.update_state)
            ```

        Parameters:
            order_id: The ID of the order
            states: Order states that will end polling. Defaults to all
                completed states.
            delay: Time (in seconds) between polls.
            max_attempts: Maximum number of polls. Set to zero for no limit.
            report: Callback function for reporting progress updates.

        Returns
            State of the order.

        Raises:
            planet.exceptions.APIException: On API error.
            planet.exceptions.ValueError: If order_id or one or more of the
                states are not valid.
            planet.exceptions.MaxAttemptsError: If the maximum number of
                attempts is reached before one of the specified states is
                reached.
        """
        invalid_states = set(states) - ORDERS_STATES_ALL
        if invalid_states:
            raise exceptions.ValueError(
                f'{invalid_states} are not valid states. '
                f'Valid states are {ORDERS_STATES_ALL}')

        num_attempts = 0
        done = False
        while not done:
            t = time.time()

            order = await self.get_order(order_id)
            state = order.state

            LOGGER.debug(state)

            if report:
                report(order.state)

            done = state in states
            if not done:
                if max_attempts:
                    num_attempts += 1
                    if num_attempts >= max_attempts:
                        raise exceptions.MaxAttemptsError(max_attempts)

                sleep_time = max(delay - (time.time() - t), 0)
                LOGGER.debug(f'sleeping {sleep_time}s')
                await asyncio.sleep(sleep_time)
        return state

    async def list_orders(
            self,
            state: str = None,
            limit: int = None,
            as_json: bool = False) -> typing.Union[typing.List[Order], dict]:
        """Get all order requests.

        Parameters:
            state: Filter orders to given state.
            limit: Limit orders to given limit.
            as_json: Return orders as a json dict.

        Returns:
            User orders that match the query

        Raises:
            planet.exceptions.APIException: On API error.
            planet.exceptions.ValueError: If state is not valid.
        """
        url = self._orders_url()
        if state:
            if state not in ORDERS_STATES_ALL:
                raise exceptions.ValueError(
                    f'Order state ({state}) is not a valid state. '
                    f'Valid states are {ORDERS_STATES_ALL}')
            params = {"state": state}
        else:
            params = None

        orders = await self._get_orders(url, params=params, limit=limit)

        if as_json:
            ret = [o.json async for o in orders]
        else:
            ret = [o async for o in orders]
        return ret

    async def _get_orders(self, url, params=None, limit=None):
        request = self._request(url, 'GET', params=params)

        return Orders(request, self._do_request, limit=limit)
