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
from typing import Any, Callable, Dict, Iterator, List, Optional

from ..http import Session
from planet.clients import TaskingClient


class TaskingAPI:
    """Tasking API client

    The Planet Tasking API is a programmatic interface that enables customers
    to manage and request high-resolution imagery collection in an efficient
    and automated way.
    """

    _client: TaskingClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production tasking API
                base url.
        """
        self._client = TaskingClient(session, base_url)

    def create_order(self, request: Dict) -> Dict:
        """Create a tasking order.

        Example:

        ```python

        from planet import Planet

        def main():
             pl = Planet()
             request = {
                 "name": "my_tasking_order",
                 "geometry": {
                     "type": "Point",
                     "coordinates": [-122.0, 37.0]
                 },
                 "products": [{
                     "item_type": "skysat_collect",
                     "asset_type": "ortho_analytic"
                 }]
             }
             order = pl.tasking.create_order(request)
        ```

        Parameters:
            request: tasking order request definition

        Returns:
            JSON description of the created tasking order

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.create_order(request))

    def get_order(self, order_id: str) -> Dict:
        """Get tasking order details by Order ID.

        Parameters:
            order_id: The ID of the tasking order

        Returns:
            JSON description of the tasking order

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.get_order(order_id))

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a tasking order.

        Parameters:
            order_id: The ID of the tasking order

        Returns:
            Results of the cancel request

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.cancel_order(order_id))

    def list_orders(self,
                    state: Optional[str] = None,
                    limit: Optional[int] = None,
                    **filters) -> Iterator[Dict]:
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
        return self._client._aiter_to_iter(
            self._client.list_orders(state=state, limit=limit, **filters))

    def wait_order(self,
                   order_id: str,
                   state: str = 'success',
                   delay: int = 5,
                   max_attempts: int = 200,
                   callback: Optional[Callable[[Dict], None]] = None) -> str:
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
        return self._client._call_sync(
            self._client.wait_order(order_id=order_id,
                                    state=state,
                                    delay=delay,
                                    max_attempts=max_attempts,
                                    callback=callback))

    def get_order_results(self, order_id: str) -> List[Dict]:
        """Get results for a completed tasking order.

        Parameters:
            order_id: Order identifier.

        Returns:
            List of result assets.

        Raises:
            planet.exceptions.ClientError: If order_id is not a valid UUID.
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(
            self._client.get_order_results(order_id))
