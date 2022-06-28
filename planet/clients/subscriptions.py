"""Planet Subscriptions API Python client."""

import itertools
import logging
from typing import AsyncIterator, Dict, Optional, Set

from httpx import URL

from planet import Session
from planet.exceptions import APIError, ClientError, PagingError
from planet.models import Paged

LOGGER = logging.getLogger()

# Collections of fake subscriptions and results for testing. Tests will
# monkeypatch these attributes.
_fake_sub_results: Dict[str, list] = {}


async def _server_subscriptions_id_results_get(subscription_id,
                                               status=None,
                                               limit=None):
    select_results = (result for result in _fake_sub_results[subscription_id]
                      if not status or result['status'] in status)
    filtered_results = itertools.islice(select_results, limit)
    for result in filtered_results:
        yield result


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

    def __init__(self, session: Optional[Session] = None) -> None:
        if session:
            self.session = session
        else:
            self.session = Session()

    async def list_subscriptions(self,
                                 status: Optional[Set[str]] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Get account subscriptions with optional filtering.

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

            # This constructor overrides Paged's and takes an httpx
            # async client as the first argument.
            def __init__(self, client, request, limit=None):
                self.request = request
                self.client = client
                self._pages = None
                self._items = []
                self.i = 0
                self.limit = limit

            # This method uses the instance's httpx client to build and
            # send requests. It's less abstracted than Paged's method.
            async def _get_pages(self):
                LOGGER.debug('getting first page')
                resp = await self.client.send(self.request)
                page = resp.json()
                yield page

                next_url = self._next_link(page)

                while (next_url):  # pragma: no branch
                    LOGGER.debug('getting next page')
                    request = self.client.build_request('GET', next_url)
                    resp = await self.client.send(request)
                    page = resp.json()
                    yield page

                    # If the next URL is the same as the previous URL we will
                    # get the same response and be stuck in a page cycle. This
                    # has happened in development and could happen in the case
                    # of a bug in the production API.
                    prev_url = next_url
                    next_url = self._next_link(page)

                    if next_url == prev_url:
                        raise PagingError(
                            "Page cycle detected at {!r}".format(next_url))

        params = {'status': [val for val in status or {}]}
        url = URL('https://api.planet.com/subscriptions/v1', params=params)
        req = self.session._client.build_request('GET', url)

        try:
            async for sub in _SubscriptionsPager(self.session._client,
                                                 req,
                                                 limit=limit):
                yield sub
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
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

        url = URL('https://api.planet.com/subscriptions/v1')
        req = self.session._client.build_request('POST', url, json=request)

        try:
            resp = await self.session._client.send(req)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
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
        url = URL(
            f'https://api.planet.com/subscriptions/v1/{subscription_id}/cancel'
        )
        req = self.session._client.build_request('POST', url)

        try:
            _ = await self.session._client.send(req)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
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
        url = URL(f'https://api.planet.com/subscriptions/v1/{subscription_id}')
        req = self.session._client.build_request('PUT', url, json=request)

        try:
            resp = await self.session._client.send(req)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
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
        url = URL(f'https://api.planet.com/subscriptions/v1/{subscription_id}')
        req = self.session._client.build_request('GET', url)

        try:
            resp = await self.session._client.send(req)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
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
            """Navigates pages of messages about subscriptions."""
            NEXT_KEY = '_next'
            ITEMS_KEY = 'results'

            # This constructor overrides Paged's and takes an httpx
            # async client as the first argument.
            def __init__(self, client, request, limit=None):
                self.request = request
                self.client = client
                self._pages = None
                self._items = []
                self.i = 0
                self.limit = limit

            # This method uses the instance's httpx client to build and
            # send requests. It's less abstracted than Paged's method.
            async def _get_pages(self):
                LOGGER.debug('getting first page')
                resp = await self.client.send(self.request)
                page = resp.json()
                yield page

                next_url = self._next_link(page)

                while (next_url):  # pragma: no branch
                    LOGGER.debug('getting next page')
                    request = self.client.build_request('GET', next_url)
                    resp = await self.client.send(request)
                    page = resp.json()
                    yield page

                    # If the next URL is the same as the previous URL we will
                    # get the same response and be stuck in a page cycle. This
                    # has happened in development and could happen in the case
                    # of a bug in the production API.
                    prev_url = next_url
                    next_url = self._next_link(page)

                    if next_url == prev_url:
                        raise PagingError(
                            "Page cycle detected at {!r}".format(next_url))

        params = {'status': [val for val in status or {}]}
        url = URL(
            'https://api.planet.com/subscriptions/v1/{subscription_id}/results',
            params=params)
        req = self.session._client.build_request('GET', url)

        try:
            async for sub in _ResultsPager(self.session._client,
                                           req,
                                           limit=limit):
                yield sub
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:
            raise
