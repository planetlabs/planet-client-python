"""Planet Subscriptions API Python client."""

import itertools
from typing import AsyncIterator, Dict, Optional, Set
import uuid

from planet.exceptions import ClientError

# Collections of fake subscriptions and results for testing. Tests will
# monkeypatch these attributes.
_fake_subs: Dict[str, dict] = {}
_fake_sub_results: Dict[str, list] = {}


async def _server_subscriptions_post(request):
    missing_keys = {'name', 'delivery', 'source'} - request.keys()
    if missing_keys:
        raise RuntimeError(f"Request lacks required members: {missing_keys!r}")

    id = str(uuid.uuid4())
    _fake_subs[id] = request
    sub = _fake_subs[id].copy()
    sub.update(id=id)
    return sub


async def _server_subscriptions_get(status=None, limit=None):
    select_subs = (dict(**sub, id=sub_id) for sub_id,
                   sub in _fake_subs.items()
                   if not status or sub['status'] in status)
    filtered_subs = itertools.islice(select_subs, limit)
    for sub in filtered_subs:
        yield sub


async def _server_subscriptions_id_cancel_post(subscription_id):
    sub = _fake_subs.pop(subscription_id)
    sub.update(id=subscription_id)
    return sub


async def _server_subscriptions_id_put(subscription_id, request):
    _fake_subs[subscription_id].update(**request)
    sub = _fake_subs[subscription_id].copy()
    sub.update(id=subscription_id)
    return sub


async def _server_subscriptions_id_get(subscription_id):
    sub = _fake_subs[subscription_id].copy()
    sub.update(id=subscription_id)
    return sub


async def _server_subscriptions_id_results_get(subscription_id,
                                               status=None,
                                               limit=None):
    select_results = (result for result in _fake_sub_results[subscription_id]
                      if not status or result['status'] in status)
    filtered_results = itertools.islice(select_results, limit)
    for result in filtered_results:
        yield result


class PlaceholderSubscriptionsClient:
    """A placeholder client.

    This class and its methods are derived from tests of a skeleton
    Subscriptions CLI. It is evolving into the real API client.

    """

    def __init__(self, session=None) -> None:
        self._session = session

    async def list_subscriptions(self,
                                 status: Optional[Set[str]] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Get account subscriptions with optional filtering.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over subcriptions, it does not return
            a list.

        Args:
            status (Set[str]): pass subscriptions with status in this
                set, filter out subscriptions with status not in this
                set.
            limit (int): limit the number of subscriptions in the
                results.
            TODO: user_id

        Yields:
            dict: a description of a subscription.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            async for sub in _server_subscriptions_get(status=status,
                                                       limit=limit):
                yield sub
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure") from server_error

    async def create_subscription(self, request: dict) -> dict:
        """Create a Subscription.

        Args:
            request (dict): description of a subscription.

        Returns:
            dict: description of created subscription.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            sub = await _server_subscriptions_post(request)
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure") from server_error
        else:
            return sub

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a Subscription.

        Args:
            subscription_id (str): id of subscription to cancel.

        Returns:
            dict: description of cancelled subscription.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            sub = await _server_subscriptions_id_cancel_post(subscription_id)
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure.") from server_error
        else:
            return sub

    async def update_subscription(self, subscription_id: str,
                                  request: dict) -> dict:
        """Update (edit) a Subscription.

        Args
            subscription_id (str): id of the subscription to update.
            request (dict): subscription content for update.

        Returns:
            dict: description of the updated subscription.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            sub = await _server_subscriptions_id_put(subscription_id, request)
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure.") from server_error
        else:
            return sub

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get a description of a Subscription.

        Args:
            subscription_id (str): id of a subscription.

        Returns:
            dict: description of the subscription.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            sub = await _server_subscriptions_id_get(subscription_id)
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure.") from server_error
        else:
            return sub

    async def get_results(self,
                          subscription_id: str,
                          status: Optional[Set[str]] = None,
                          limit: int = 100) -> AsyncIterator[dict]:
        """Get Results of a Subscription.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Args:
            subscription_id (str): id of a subscription.
            status (Set[str]): pass result with status in this set,
                filter out results with status not in this set.
            limit (int): limit the number of subscriptions in the
                results.
            TODO: created, updated, completed, user_id

        Yields:
            dict: description of a subscription results.

        Raises:
            ClientError

        """
        try:
            # TODO: replace with httpx request.
            async for result in _server_subscriptions_id_results_get(
                    subscription_id, status=status, limit=limit):
                yield result
        except Exception as server_error:
            # TODO: remove "from server_error" clause. It's useful
            # during development but may invite users to depend on the
            # value of server_error.
            raise ClientError("Subscription failure.") from server_error
