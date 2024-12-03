from typing import Optional
from planet.auth import AuthType
from planet.clients.data import DataAPI
from planet.clients.orders import OrdersAPI
from planet.clients.subscriptions import SubscriptionsAPI, SubscriptionsClient
from planet.http import Session

SYNC_CLIENT_AGENT = "python-sdk-sync"


class Planet:
    """Planet API client. This client contains non-async methods.

    Authentication is required: defaults to detecting API key from environment (PL_API_KEY).

    Members:
    `data`: for interacting with the Planet Data API.
    `orders`: Orders API.
    `subscriptions`: Subscriptions API.

    Quick start example:
    ```python
    # requires PL_API_KEY

    pl = Planet()
    for item in pl.data.search(['PSScene'], limit=5):
        print(item)

    for sub in pl.subscriptions.list_subscriptions():
        print(item)
    ```

    Parameters:
        auth: Optional authentication config. defaults to detecting from environment (PL_API_KEY).
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session or Session()
        self._session._client.headers.update({"X-Planet-App": SYNC_CLIENT_AGENT})

        self.data = DataAPI(self._session)
        self.orders = OrdersAPI(self._session)
        self.subscriptions = SubscriptionsAPI(self._session)

