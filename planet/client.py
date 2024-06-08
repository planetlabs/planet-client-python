import asyncio
from typing import Dict, Iterator, List, Optional
from planet.auth import AuthType
from planet.clients.data import DataClient
from planet.clients.orders import OrdersClient
from planet.clients.subscriptions import SubscriptionsClient
from planet.http import Session

SYNC_CLIENT_AGENT = "python-sdk-sync"


class Planet:
    """Planet API client (synchronous).

    Quick start example:
    ```python

    client = Planet()
    for item in client.search(['PSScene'], limit=5):
        print(item)
    ```

    Parameters:
        auth: Authentication config. defaults to detecting from environment (PL_API_KEY).
    """

    def __init__(self, auth: Optional[AuthType] = None) -> None:
        self._session = Session(auth)
        self._session._client.headers.update({"X-Planet-App": SYNC_CLIENT_AGENT})

        self._data = DataClient(self._session)
        self._orders = OrdersClient(self._session)
        self._subscriptions = SubscriptionsClient(self._session)

        self.auth = auth

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
        client = Planet()
        for item in client.search(['PSScene'], limit=5):
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

        results = self._data.search(
            item_types, search_filter, name, sort, limit, geometry
        )

        try:
            while True:
                yield asyncio.run(results.__anext__())
        except StopAsyncIteration:
            pass


    def create_order(self, request: Dict) -> Dict:
        """Create an order.

        Example:

        ```python

        from planet import Planet
        from planet.order_request import build_request, product
        
        def main():
             client = Planet()
             image_ids = ["20200925_161029_69_2223"]
             request = build_request(
                 'test_order',
                 [product(image_ids, 'analytic_udm2', 'psscene')]
             )
             order = client.create_order(request)
        ```

        Parameters:
            request: order request definition

        Returns:
            JSON description of the created order

        Raises:
            planet.exceptions.APIError: On API error.
        """
        return asyncio.run(self._orders.create_order(request))

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
        return asyncio.run(self._orders.get_order(order_id))

