from typing import Optional
from .data import DataAPI
from .orders import OrdersAPI
from .subscriptions import SubscriptionsAPI
from planet.http import Session
from planet.__version__ import __version__

SYNC_CLIENT_X_PLANET_APP = "python-sdk-sync"


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
        session: Optional Session. The Session can be provided allowing for customization, and
            will default to standard behavior when not provided. Example:

          ```python
          from planet.sync import Planet

          pl = Planet()
          ````
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session or Session()
        self._session._client.headers.update({
            "X-Planet-App":
            SYNC_CLIENT_X_PLANET_APP,
            "User-Agent":
            f"planet-client-python/{__version__}/sync"
        })

        self.data = DataAPI(self._session)
        self.orders = OrdersAPI(self._session)
        self.subscriptions = SubscriptionsAPI(self._session)
