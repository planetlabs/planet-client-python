"""Planet Subscriptions API Python client."""

import logging
from typing import AsyncIterator, Optional, Set

from planet.exceptions import APIError, ClientError
from ..constants import PLANET_BASE_URL
from planet.http import Session
from planet.models import Paged, Request, Response

BASE_URL = f'{PLANET_BASE_URL}/subscriptions/v1'

LOGGER = logging.getLogger()


class Results(Paged):
    """Navigates pages of messages about subscription results."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'results'


class Subscriptions(Paged):
    """Navigates pages of messages about subscriptions."""
    ITEMS_KEY = 'subscriptions'


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

        self._base_url = BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def _request(self, url, method, data=None, params=None, json=None):
        return Request(url, method=method, data=data, params=params, json=json)

    async def _do_request(self, request: Request) -> Response:
        """Submit a request and get response.

        Parameters:
            request: request to submit
        """
        return await self._session.request(request)

    async def list_subscriptions(self,
                                 status: Optional[Set[str]] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Get account subscriptions with optional filtering.

        Note:
            The name of this method is based on the API's method name.
            This method returns an iterator over subcriptions, it does
            not return a list.

        Args:
            status: pass subscriptions with status in this
                set, filter out subscriptions with status not in this
                set.
            limit: Maximum number of results to return.
            TODO: user_id

        Returns:
            An iterator over descriptions of subscriptions.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = {'status': [val for val in status or {}]}
        url = 'https://api.planet.com/subscriptions/v1'
        request = self._request(url, method='GET', params=params)

        try:
            return Subscriptions(request, self._do_request, limit=limit)
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
        url = 'http://www.MockNotRealURL.com/api/path'
        req = self._request('POST', url, json=request)
        # LOGGER.warning(BASE_URL)
        try:
            resp = await self._do_request(req)
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
        req = self._request('POST', f'{BASE_URL}/{subscription_id}/cancel')

        try:
            _ = await self._do_request(req)
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
        url = f'{BASE_URL}{subscription_id}'
        req = self._request('PUT', url)

        try:
            resp = await self._do_request(req)
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
        url = f'{BASE_URL}/{subscription_id}'

        req = self._request(url, method='GET')
        try:
            resp = await self._do_request(req)
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
        """Get Results of a Subscription.

        Note:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Args:
            subscription_id: id of a subscription.
            status: pass result with status in this set,
                filter out results with status not in this set.
            limit: Maximum number of results to return. Set to zero to return
                all results.
            TODO: created, updated, completed, user_id

        Returns:
            Iterator over descriptions of a subscription results.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = {'status': [val for val in status or {}]}
        url = f'{BASE_URL}/{subscription_id}/results'

        request = self._request(url, method='GET', params=params)
        try:
            return Results(request, self._do_request, limit=limit)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
