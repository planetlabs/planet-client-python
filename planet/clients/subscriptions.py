"""Planet Subscriptions API Python client."""

import logging
from typing import AsyncIterator, Optional, Set

from planet.exceptions import APIError, ClientError
from planet.http import Session
from planet.models import Paged

LOGGER = logging.getLogger()


class SubscriptionsClient:
    """A Planet Subscriptions Service API 1.0.0 client.

    The methods of this class forward request parameters to the
    operations described in the Planet Subscriptions Service API 1.0.0
    (https://api.planet.com/subscriptions/v1/spec) using HTTP 1.1.

    The methods generally return or yield Python dicts with the same
    structure as the JSON messages used by the service API. Many of the
    exceptions raised by this class are categorized by HTTP client
    (4xx) or server (5xx) errors. This client's level of abstraction is
    low.

    Attributes:
        session (Session): an authenticated session which wraps the
            low-level HTTP client.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def list_subscriptions(self,
                                 status: Optional[Set[str]] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Iterate over list of account subscriptions with optional filtering.

        Note:
            The name of this method is based on the API's method name.
            This method provides iteration over subcriptions, it does
            not return a list.

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
            APIError: on an API server error.
            ClientError: on a client error.
        """

        class _SubscriptionsPager(Paged):
            """Navigates pages of messages about subscriptions."""
            ITEMS_KEY = 'subscriptions'

        params = {'status': [val for val in status or {}]}
        url = 'https://api.planet.com/subscriptions/v1'

        try:
            response = await self._session.request(method='GET',
                                                   url=url,
                                                   params=params)
            async for sub in _SubscriptionsPager(response,
                                                 self._session.request,
                                                 limit=limit):
                yield sub
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def create_subscription(self, request: dict) -> dict:
        """Create a Subscription.

        Args:
            request (dict): description of a subscription.

        Returns:
            dict: description of created subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """

        url = 'https://api.planet.com/subscriptions/v1'

        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            sub = resp.json()
            return sub

    async def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel a Subscription.

        Args:
            subscription_id (str): id of subscription to cancel.

        Returns:
            None

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        root_url = 'https://api.planet.com/subscriptions/v1'
        url = f'{root_url}/{subscription_id}/cancel'

        try:
            _ = await self._session.request(method='POST', url=url)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def update_subscription(self, subscription_id: str,
                                  request: dict) -> dict:
        """Update (edit) a Subscription.

        Args
            subscription_id (str): id of the subscription to update.
            request (dict): subscription content for update.

        Returns:
            dict: description of the updated subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'https://api.planet.com/subscriptions/v1/{subscription_id}'

        try:
            resp = await self._session.request(method='PUT',
                                               url=url,
                                               json=request)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            sub = resp.json()
            return sub

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get a description of a Subscription.

        Args:
            subscription_id (str): id of a subscription.

        Returns:
            dict: description of the subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'https://api.planet.com/subscriptions/v1/{subscription_id}'

        try:
            resp = await self._session.request(method='GET', url=url)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            sub = resp.json()
            return sub

    async def get_results(self,
                          subscription_id: str,
                          status: Optional[Set[str]] = None,
                          limit: int = 100) -> AsyncIterator[dict]:
        """Iterate over results of a Subscription.

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
            APIError: on an API server error.
            ClientError: on a client error.
        """

        class _ResultsPager(Paged):
            """Navigates pages of messages about subscription results."""
            ITEMS_KEY = 'results'

        params = {'status': [val for val in status or {}]}
        root_url = 'https://api.planet.com/subscriptions/v1'
        url = f'{root_url}/{subscription_id}/results'

        try:
            resp = await self._session.request(method='GET',
                                               url=url,
                                               params=params)

            async for sub in _ResultsPager(resp,
                                           self._session.request,
                                           limit=limit):
                yield sub
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
