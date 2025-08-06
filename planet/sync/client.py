from typing import Optional

from .features import FeaturesAPI
from .data import DataAPI
from .destinations import DestinationsAPI
from .orders import OrdersAPI
from .subscriptions import SubscriptionsAPI
from planet.http import Session
from planet.__version__ import __version__
from planet.constants import PLANET_BASE_URL

SYNC_CLIENT_X_PLANET_APP = "python-sdk-sync"


class Planet:
    """Planet API client. This client contains non-async methods.

    Authentication is required: defaults to detecting API key from environment (PL_API_KEY).

    Members:

    - `data`: for interacting with the Planet Data API.
    - `destinations`: Destinations API.
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
        base_url: Optional base URL for Planet APIs. Defaults to (https://api.planet.com).
            Each API will append its specific path suffix (/data/v1, /compute/ops, etc.).

    """

    def __init__(self,
                 session: Optional[Session] = None,
                 base_url: Optional[str] = None) -> None:
        self._session = session or Session()
        self._session._client.headers.update({
            "X-Planet-App": SYNC_CLIENT_X_PLANET_APP,
            "User-Agent": f"planet-client-python/{__version__}/sync",
        })

        # Use provided base URL or default
        planet_base = base_url or PLANET_BASE_URL

        # Create API instances with service-specific URL paths
        self.data = DataAPI(self._session, f"{planet_base}/data/v1/")
        self.destinations = DestinationsAPI(self._session,
                                            f"{planet_base}/destinations/v1")
        self.orders = OrdersAPI(self._session, f"{planet_base}/compute/ops")
        self.subscriptions = SubscriptionsAPI(
            self._session, f"{planet_base}/subscriptions/v1/")
        self.features = FeaturesAPI(self._session,
                                    f"{planet_base}/features/v1/ogc/my/")
