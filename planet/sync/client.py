from typing import Optional

from .features import FeaturesAPI
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

    - `data`: for interacting with the Planet Data API.
    - `orders`: Orders API.
    - `subscriptions`: Subscriptions API.
    - `features`: Features API

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
            will default to standard behavior when not provided.
        data_base_url: Optional base URL for Data API. Defaults to production.
        orders_base_url: Optional base URL for Orders API. Defaults to production.
        subscriptions_base_url: Optional base URL for Subscriptions API. Defaults to production.
        features_base_url: Optional base URL for Features API. Defaults to production.

    """

    def __init__(self,
                 session: Optional[Session] = None,
                 data_base_url: Optional[str] = None,
                 orders_base_url: Optional[str] = None,
                 subscriptions_base_url: Optional[str] = None,
                 features_base_url: Optional[str] = None) -> None:
        self._session = session or Session()
        self._session._client.headers.update({
            "X-Planet-App": SYNC_CLIENT_X_PLANET_APP,
            "User-Agent": f"planet-client-python/{__version__}/sync",
        })

        self.data = DataAPI(self._session, data_base_url)
        self.orders = OrdersAPI(self._session, orders_base_url)
        self.subscriptions = SubscriptionsAPI(self._session,
                                              subscriptions_base_url)
        self.features = FeaturesAPI(self._session, features_base_url)
