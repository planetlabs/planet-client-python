from typing import Optional
from planet.clients.data import DataAPI
from planet.clients.orders import OrdersAPI
from planet.clients.subscriptions import SubscriptionsAPI
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
        session: Optional Session. If not provided, a new session is created.
          The session can be used to control the authentication method. Example:

          ```python
          from planet import Auth, Session, Planet

          auth = Auth.from_key('examplekey')
          session = Session(auth=auth)
          pl = Planet(session=session)
          ````
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session or Session()
        self._session._client.headers.update(
            {"X-Planet-App": SYNC_CLIENT_AGENT})

        self.data = DataAPI(self._session)
        self.orders = OrdersAPI(self._session)
        self.subscriptions = SubscriptionsAPI(self._session)
