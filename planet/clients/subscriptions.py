"""Planet Subscriptions API Python client."""

import itertools
from typing import AsyncIterator, Dict, Set
import uuid

from planet.exceptions import PlanetError

# Collections of fake subscriptions and results for testing. Tests will
# monkeypatch these attributes.
_fake_subs: Dict[str, dict] = {}
_fake_sub_results: Dict[str, list] = {}


class PlaceholderSubscriptionsClient:
    """A placeholder client.

    This class and its methods are derived from tests of a skeleton
    Subscriptions CLI.

    """

    def __init__(self, session=None) -> None:
        self._session = session

    async def list_subscriptions(self,
                                 status: Set[str] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Get Subscriptions.

        Parameters:
            status
            limit

        Yields:
            dict

        """
        if status:
            select_subs = (dict(**sub, id=sub_id) for sub_id,
                           sub in _fake_subs.items()
                           if sub['status'] in status)
        else:
            select_subs = (
                dict(**sub, id=sub_id) for sub_id, sub in _fake_subs.items())

        filtered_subs = itertools.islice(select_subs, limit)

        for sub in filtered_subs:
            yield sub

    async def create_subscription(self, request: dict) -> dict:
        """Create a Subscription.

        Parameters:
            request

        Returns:
            dict

        Raises:
            PlanetError

        """
        missing_keys = {'name', 'delivery', 'source'} - request.keys()
        if missing_keys:
            raise PlanetError(
                f"Request lacks required members: {missing_keys!r}")

        id = str(uuid.uuid4())
        _fake_subs[id] = request
        sub = _fake_subs[id].copy()
        sub.update(id=id)
        return sub

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            sub = _fake_subs.pop(subscription_id)
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def update_subscription(self, subscription_id: str,
                                  request: dict) -> dict:
        """Update (edit) a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            _fake_subs[subscription_id].update(**request)
            sub = _fake_subs[subscription_id].copy()
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get a description of a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            sub = _fake_subs[subscription_id].copy()
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def list_subscription_results(
            self,
            subscription_id: str,
            status: Set[str] = None,
            limit: int = 100) -> AsyncIterator[dict]:
        """Get Results of a Subscription.

        Parameters:
            subscription_id
            status
            limit

        Yields:
            dict

        Raises:
            PlanetError

        """
        try:
            if status:
                select_results = (
                    result for result in _fake_sub_results[subscription_id]
                    if result['status'] in status)
            else:
                select_results = (
                    result for result in _fake_sub_results[subscription_id])

            filtered_results = itertools.islice(select_results, limit)
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        for result in filtered_results:
            yield result
