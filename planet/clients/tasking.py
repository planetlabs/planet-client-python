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
"""Functionality for interacting with the tasking api"""
import asyncio
import logging
from typing import AsyncIterator, Callable, List, Optional, TypeVar
import uuid

from planet.clients.base import _BaseClient
from .. import exceptions
from ..constants import PLANET_BASE_URL
from ..http import Session
from ..models import Paged

BASE_URL = f'{PLANET_BASE_URL}/tasking/v2/'
ORDERS_PATH = 'orders'

# Tasking order states - similar to orders API but for tasking
TASKING_ORDER_STATE_SEQUENCE = \
    ('queued', 'running', 'success', 'failed', 'cancelled')

WAIT_DELAY = 5
WAIT_MAX_ATTEMPTS = 200

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class TaskingOrders(Paged):
    """Asynchronous iterator over tasking orders from a paged response."""
    ITEMS_KEY = 'orders'


class TaskingOrderStates:
    """Helper class for working with tasking order states."""
    SEQUENCE = TASKING_ORDER_STATE_SEQUENCE

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


class TaskingClient(_BaseClient):
    """High-level asynchronous access to Planet's Tasking API.

    The Planet Tasking API is a programmatic interface that enables customers
    to manage and request high-resolution imagery collection in an efficient
    and automated way.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('tasking')
        ...         # use client here
        ...
        >>> asyncio.run(main())

        ```
    """

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production tasking API
                base url.
        """
        super().__init__(session, base_url or BASE_URL)

    @staticmethod
    def _check_order_id(oid):
        """Raises planet.exceptions.ClientError if oid is not a valid UUID"""
        try:
            uuid.UUID(oid)
        except (ValueError, AttributeError, TypeError):
            msg = f'Tasking order id ({oid}) is not a valid UUID hexadecimal string.'
            raise exceptions.ClientError(msg)

    def _orders_url(self, order_id: Optional[str] = None):
        """Build orders URL with optional order ID."""
        url = f'{self._base_url}{ORDERS_PATH}'
        if order_id:
            url = f'{url}/{order_id}'
        return url

    async def create_order(self, request: dict) -> dict:
        """Create a tasking order request.

        Example:

        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     request = {
        ...         "name": "my_tasking_order",
        ...         "geometry": {
        ...             "type": "Point",
        ...             "coordinates": [-122.0, 37.0]
        ...         },
        ...         "products": [{
        ...             "item_type": "skysat_collect",
        ...             "asset_type": "ortho_analytic"
        ...         }]
        ...     }
        ...     async with Session() as sess:
        ...         cl = sess.client('tasking')
        ...         order = await cl.create_order(request)
        ...
        >>> asyncio.run(main())
        ```

        Parameters:
            request: tasking order request definition

        Returns:
            JSON description of the created tasking order

        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._orders_url()
        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def get_order(self, order_id: str) -> dict:
        """Get a tasking order.

        Parameters:
            order_id: Order identifier.

        Returns:
            JSON description of the tasking order.

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)
        url = self._orders_url(order_id)
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel a tasking order.

        Parameters:
            order_id: Order identifier.

        Returns:
            JSON description of the cancelled tasking order.

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)
        url = self._orders_url(order_id)
        # Cancel is typically done via PATCH or PUT with state change
        response = await self._session.request(method='PATCH',
                                               url=url,
                                               json={'state': 'cancelled'})
        return response.json()

    async def list_orders(self,
                          state: Optional[str] = None,
                          limit: Optional[int] = None,
                          **filters) -> AsyncIterator[dict]:
        """Iterate over tasking orders.

        Parameters:
            state: Filter by order state
            limit: Maximum number of orders to return
            **filters: Additional query parameters

        Yields:
            Tasking order description

        Raises:
            planet.exceptions.APIError: On API error.
        """
        params = {}
        if state:
            params['state'] = state
        params.update(filters)

        url = self._orders_url()
        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for order in TaskingOrders(response, self._session.request, limit=limit or 0):
            yield order

    async def wait_order(
            self,
            order_id: str,
            state: str = 'success',
            delay: int = WAIT_DELAY,
            max_attempts: int = WAIT_MAX_ATTEMPTS,
            callback: Optional[Callable[[dict], None]] = None) -> str:
        """Wait for a tasking order to reach a specified state.

        Parameters:
            order_id: Order identifier.
            state: Desired order state. Default is 'success'.
            delay: Time (in seconds) between polls. Default is 5.
            max_attempts: Maximum number of attempts. Default is 200.
            callback: Function that handles order description.

        Returns:
            Final state of order.

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID
                or state is not in the state sequence.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)

        if state not in TaskingOrderStates.SEQUENCE:
            raise exceptions.ClientError(f'{state} not a valid order state')

        # Check if we have passed the state we are waiting for
        order = await self.get_order(order_id)
        current_state = order['state']

        if callback:
            callback(order)

        if TaskingOrderStates.passed(state, current_state):
            return current_state

        # Poll until state reached
        attempt = 0
        while not TaskingOrderStates.reached(state, current_state):

            LOGGER.debug(f'Order {order_id} state: {current_state}. '
                         f'Waiting for {state}.')

            if attempt >= max_attempts:
                raise exceptions.APIError(
                    f'Maximum attempts reached waiting for order {order_id}')

            if TaskingOrderStates.is_final(current_state):
                return current_state

            attempt += 1
            await asyncio.sleep(delay)

            order = await self.get_order(order_id)
            current_state = order['state']

            if callback:
                callback(order)

        return current_state

    async def get_order_results(self, order_id: str) -> List[dict]:
        """Get results for a completed tasking order.

        Parameters:
            order_id: Order identifier.

        Returns:
            List of result assets.

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        self._check_order_id(order_id)
        url = f'{self._orders_url(order_id)}/results'
        response = await self._session.request(method='GET', url=url)
        return response.json().get('results', [])
