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

from .. import constants, exceptions
from ..http import Session
from ..models import Order, Orders, Request, Response, StreamingBody


BASE_URL = constants.PLANET_BASE_URL + 'compute/ops/'
STATS_PATH = 'stats/orders/v2/'
ORDERS_PATH = 'orders/v2/'
BULK_PATH = 'bulk/orders/v2/'

# Order states https://developers.planet.com/docs/orders/ordering/#order-states
ORDERS_STATES_COMPLETE = ['success', 'partial', 'cancelled', 'failed']
ORDERS_STATES_IN_PROGRESS = ['queued', 'running']
ORDERS_STATES = ORDERS_STATES_IN_PROGRESS + ORDERS_STATES_COMPLETE

LOGGER = logging.getLogger(__name__)


class OrdersClientException(Exception):
    """Exceptions thrown by OrdersClient"""
    pass


class OrdersClient():
    """High-level asynchronous access to Planet's orders API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session, OrdersClient
        >>>
        >>> async def main():
        ...     auth = ('example_api_key', '')
        ...     async with Session(auth=auth) as sess:
        ...         cl = OrdersClient(sess)
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```


    """
    def __init__(
        self,
        session: Session,
        base_url: str = None
    ):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production orders API
                base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if not self._base_url.endswith('/'):
            self._base_url += '/'

    @staticmethod
    def _check_order_id(oid):
        msg = f'Order id ({oid}) must be a valid UUID string.'
        if not isinstance(oid, str):
            raise OrdersClientException(msg)

        try:
            uuid.UUID(oid)
        except ValueError:
            raise OrdersClientException(msg)

    def _orders_url(self):
        return self._base_url + ORDERS_PATH

    def _stats_url(self):
        return self._base_url + STATS_PATH

    def _order_url(self, order_id):
        self._check_order_id(order_id)
        return self._orders_url() + order_id

    def _bulk_url(self):
        return self._base_url + BULK_PATH

    def _request(self, url, method, data=None, params=None, json=None):
        return Request(url, method=method, data=data, params=params, json=json)

    async def _do_request(
        self,
        request: Request
    ) -> Response:
        '''Submit a request and get response.

        Parameters:
            request: request to submit
        '''
        return await self._session.request(request)

    async def create_order(
        self,
        request: dict
    ) -> str:
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

    async def get_order(
        self,
        order_id: str
    ) -> Order:
        '''Get order details by Order ID.

        Parameters:
            order_id: The ID of the order

        Returns:
            Order information

        Raises:
            OrdersClientException: If order_id is not valid UUID.
            planet.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)

        req = self._request(url, method='GET')

        try:
            resp = await self._do_request(req)
        except exceptions.MissingResource as ex:
            msg_json = json.loads(ex.message)
            msg = msg_json['message']
            raise exceptions.MissingResource(msg)

        order = Order(resp.json())
        return order

    async def cancel_order(
        self,
        order_id: str
    ) -> Response:
        '''Cancel a queued order.

        **Note:** According to the API docs, cancel order should return the
        cancelled order details. But testing reveals that an empty response is
        returned upon success.

        Parameters:
            order_id: The ID of the order

        Returns:
            Empty response

        Raises:
            OrdersClientException: If order_id is not valid UUID.
            planet.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        req = self._request(url, method='PUT')

        try:
            await self._do_request(req)
        except exceptions.Conflict as ex:
            msg = json.loads(ex.message)['message']
            raise exceptions.Conflict(msg)
        except exceptions.MissingResource as ex:
            msg = json.loads(ex.message)['message']
            raise exceptions.MissingResource(msg)

    async def cancel_orders(
        self,
        order_ids: typing.List[str] = None
    ) -> dict:
        '''Cancel queued orders in bulk.

        Parameters:
            order_ids: The IDs of the orders. If empty or None, all orders in a
                pre-running state will be cancelled.

        Returns:
            Results of the bulk cancel request

        Raises:
            planet.exceptions.APIException: On API error.
        '''
        url = self._bulk_url() + 'cancel'
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

    async def download_asset(
        self,
        location: str,
        filename: str = None,
        directory: str = None,
        overwrite: bool = False,
        progress_bar: bool = True
    ) -> str:
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

    async def download_order(
        self,
        order_id: str,
        directory: str = None,
        overwrite: bool = False,
        progress_bar: bool = False
    ) -> typing.List[str]:
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
        """
        order = await self.get_order(order_id)
        locations = order.locations
        LOGGER.info(
            f'downloading {len(locations)} assets from order {order_id}'
        )
        filenames = [await self.download_asset(location,
                                               directory=directory,
                                               overwrite=overwrite,
                                               progress_bar=progress_bar)
                     for location in locations]
        return filenames

    async def poll(
        self,
        order_id: str,
        state: str = None,
        wait: int = 1,
        report=None
    ) -> str:
        """Poll for order status until order reaches desired state, optionally
        reporting status.

        By default, the Orders API is polled every 1 second for status updates.
        The API rate limit for this endpoint is 10 requests per second.
        If many orders are being polled asynchronously, consider
        increasing the wait to avoid throttling.

        Example:
            ```python
            from planet.reporting import StateBar

            with StateBar() as bar:
                await poll(order_id, report=bar.update)
            ```

        Parameters:
            order_id: The ID of the order
            state: State to poll until. If multiple, use list. Defaults to
                any completed state.
            wait: Time (in seconds) between polls.
            report: Callback function for progress updates. Invoked with
                keyword arguments `state` (poll state) and `logger`
                (callback for logging progress bar status). Recommended
                value is `reporting.StateBar.update`.

        Returns
            Completed state of the order.

        Raises:
            planet.exceptions.APIException: On API error.
            OrdersClientException: If order_id is not valid or state is not
                supported.
        """
        if state:
            if state not in ORDERS_STATES:
                raise OrdersClientException(
                    f'{state} should be one of'
                    f'{ORDERS_STATES}')
            states = [state]
        else:
            states = ORDERS_STATES_COMPLETE

        completed = False
        while not completed:
            t = time.time()

            order = await self.get_order(order_id)
            state = order.state

            if report:
                report(state=order.state)
            else:
                LOGGER.debug(state)

            completed = state in states
            if not completed:
                sleep_time = max(wait-(time.time()-t), 0)
                LOGGER.debug(f'sleeping {sleep_time}s')
                await asyncio.sleep(sleep_time)
        return state

    async def list_orders(
        self,
        state: str = None,
        limit: int = None,
        as_json: bool = False
    ) -> typing.Union[typing.List[Order], dict]:
        """Get all order requests.

        Parameters:
            state: Filter orders to given state.
            limit: Limit orders to given limit.
            as_json: Return orders as a json dict.

        Returns:
            User orders that match the query

        Raises:
            planet.exceptions.APIException: On API error.
        """
        url = self._orders_url()
        if state:
            self._check_state(state)
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

    @staticmethod
    def _check_state(state):
        if state not in ORDERS_STATES:
            raise OrdersClientException(
                f'Order state (\'{state}\') should be one of: '
                f'{ORDERS_STATES}'
            )
