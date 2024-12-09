"""Planet Subscriptions API Python client."""

import logging
from typing import AsyncIterator, Optional, Sequence, Dict, Union

from typing_extensions import Literal

from planet.exceptions import APIError, ClientError
from planet.http import Session
from planet.models import Paged
from ..constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/subscriptions/v1/'

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

    High-level asynchronous access to Planet's subscriptions API:

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('subscriptions')
        ...         # use client here
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production subscriptions
                API base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    async def list_subscriptions(
            self,
            status: Optional[Sequence[str]] = None,
            limit: int = 100,
            created: Optional[str] = None,
            end_time: Optional[str] = None,
            hosting: Optional[bool] = None,
            name__contains: Optional[str] = None,
            name: Optional[str] = None,
            source_type: Optional[str] = None,
            start_time: Optional[str] = None,
            sort_by: Optional[str] = None,
            updated: Optional[str] = None) -> AsyncIterator[dict]:
        """Iterate over list of account subscriptions with optional filtering and sorting.

        Note:
            The name of this method is based on the API's method name.
            This method provides iteration over subcriptions, it does
            not return a list.

        Args:
            created (str): filter by created time or interval.
            end_time (str): filter by end time or interval.
            hosting (bool): only return subscriptions that contain a
                hosting block (e.g. SentinelHub hosting).
            name__contains (str): only return subscriptions with a
                name that contains the given string.
            name (str): filter by name.
            source_type (str): filter by source type.
            start_time (str): filter by start time or interval.
            status (Set[str]): include subscriptions with a status in this set.
            sort_by (str): fields to sort subscriptions by. Multiple
                fields can be specified, separated by commas. The sort
                direction can be specified by appending ' ASC' or '
                DESC' to the field name. The default sort direction is
                ascending. When multiple fields are specified, the sort
                order is applied in the order the fields are listed.

                Supported fields: name, created, updated, start_time, end_time

                Examples:
                 * "name"
                 * "name DESC"
                 * "name,end_time DESC,start_time"
            updated (str): filter by updated time or interval.
            limit (int): limit the number of subscriptions in the
                results. When set to 0, no maximum is applied.
            TODO: user_id

        Datetime args (created, end_time, start_time, updated) can either be a
        date-time or an interval, open or closed. Date and time expressions adhere
        to RFC 3339. Open intervals are expressed using double-dots.

        Examples:
            * A date-time: "2018-02-12T23:20:50Z"
            * A closed interval: "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z"
            * Open intervals: "2018-02-12T00:00:00Z/.." or "../2018-03-18T12:31:12Z"

        Yields:
            dict: a description of a subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """

        class _SubscriptionsPager(Paged):
            """Navigates pages of messages about subscriptions."""
            ITEMS_KEY = 'subscriptions'

        params: Dict[str, Union[str, Sequence[str], bool]] = {}
        if created is not None:
            params['created'] = created
        if end_time is not None:
            params['end_time'] = end_time
        if hosting is not None:
            params['hosting'] = hosting
        if name__contains is not None:
            params['name__contains'] = name__contains
        if name is not None:
            params['name'] = name
        if source_type is not None:
            params['source_type'] = source_type
        if start_time is not None:
            params['start_time'] = start_time
        if status is not None:
            params['status'] = [val for val in status]
        if sort_by is not None:
            params['sort_by'] = sort_by
        if updated is not None:
            params['updated'] = updated

        try:
            response = await self._session.request(method='GET',
                                                   url=self._base_url,
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

        try:
            resp = await self._session.request(method='POST',
                                               url=self._base_url,
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
        url = f'{self._base_url}/{subscription_id}/cancel'

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
        """Update (edit) a Subscription via PUT.

        Args
            subscription_id (str): id of the subscription to update.
            request (dict): subscription content for update, full
                payload is required.

        Returns:
            dict: description of the updated subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/{subscription_id}'

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

    async def patch_subscription(self, subscription_id: str,
                                 request: dict) -> dict:
        """Update (edit) a Subscription via PATCH.

        Args
            subscription_id (str): id of the subscription to update.
            request (dict): subscription content for update, only
                attributes to update are required.

        Returns:
            dict: description of the updated subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/{subscription_id}'

        try:
            resp = await self._session.request(method='PATCH',
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
        url = f'{self._base_url}/{subscription_id}'

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
                          status: Optional[Sequence[Literal[
                              "created",
                              "queued",
                              "processing",
                              "failed",
                              "success"]]] = None,
                          limit: int = 100) -> AsyncIterator[dict]:
        """Iterate over results of a Subscription.

        Notes:
            The name of this method is based on the API's method name. This
            method provides iteration over results, it does not get a
            single result description or return a list of descriptions.

        Parameters:
            subscription_id (str): id of a subscription.
            status (Set[str]): pass result with status in this set,
                filter out results with status not in this set.
            limit (int): limit the number of subscriptions in the
                results. When set to 0, no maximum is applied.
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
        url = f'{self._base_url}/{subscription_id}/results'

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

    async def get_results_csv(
        self,
        subscription_id: str,
        status: Optional[Sequence[Literal["created",
                                          "queued",
                                          "processing",
                                          "failed",
                                          "success"]]] = None
    ) -> AsyncIterator[str]:
        """Iterate over rows of results CSV for a Subscription.

        Parameters:
            subscription_id (str): id of a subscription.
            status (Set[str]): pass result with status in this set,
                filter out results with status not in this set.
            TODO: created, updated, completed, user_id

        Yields:
            str: a row from a CSV file.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/{subscription_id}/results'
        params = {'status': [val for val in status or {}], 'format': 'csv'}

        # Note: retries are not implemented yet. This project has
        # retry logic for HTTP requests, but does not handle errors
        # during streaming. We may want to consider a retry decorator
        # for this entire method a la stamina:
        # https://github.com/hynek/stamina.
        async with self._session._client.stream('GET', url,
                                                params=params) as response:
            async for line in response.aiter_lines():
                yield line
