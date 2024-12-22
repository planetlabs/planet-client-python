"""Planet Subscriptions API Python client."""

from typing import Any, Dict, Iterator, Optional, Sequence, Union

from typing_extensions import Literal

from planet.http import Session
from planet.clients import SubscriptionsClient


class SubscriptionsAPI:
    """Subscriptions API client

    Example:
        ```python
        >>> from planet import Planet
        >>>
        >>> pl = Planet()
        >>> pl.subscriptions.list_subscriptions()
        ```
    """

    _client: SubscriptionsClient

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production subscriptions
                API base url.
        """

        self._client = SubscriptionsClient(session, base_url)

    def list_subscriptions(self,
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
                           updated: Optional[str] = None) -> Iterator[dict]:
        """Iterate over list of account subscriptions with optional filtering.

        Note:
            The name of this method is based on the API's method name.
            This method provides iteration over subscriptions, it does
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

        results = self._client.list_subscriptions(status,
                                                  limit,
                                                  created,
                                                  end_time,
                                                  hosting,
                                                  name__contains,
                                                  name,
                                                  source_type,
                                                  start_time,
                                                  sort_by,
                                                  updated)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass

    def create_subscription(self, request: Dict) -> Dict:
        """Create a Subscription.

        Args:
            request (dict): description of a subscription.

        Returns:
            dict: description of created subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        return self._client._call_sync(
            self._client.create_subscription(request))

    def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel a Subscription.

        Args:
            subscription_id (str): id of subscription to cancel.

        Returns:
            None

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        return self._client._call_sync(
            self._client.cancel_subscription(subscription_id))

    def update_subscription(self, subscription_id: str, request: dict) -> dict:
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
        return self._client._call_sync(
            self._client.update_subscription(subscription_id, request))

    def patch_subscription(self, subscription_id: str,
                           request: Dict[str, Any]) -> Dict[str, Any]:
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
        return self._client._call_sync(
            self._client.patch_subscription(subscription_id, request))

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get a description of a Subscription.

        Args:
            subscription_id (str): id of a subscription.

        Returns:
            dict: description of the subscription.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        return self._client._call_sync(
            self._client.get_subscription(subscription_id))

    def get_results(
        self,
        subscription_id: str,
        status: Optional[Sequence[Literal["created",
                                          "queued",
                                          "processing",
                                          "failed",
                                          "success"]]] = None,
        limit: int = 100,
    ) -> Iterator[Union[Dict[str, Any], str]]:
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
        results = self._client.get_results(subscription_id, status, limit)

        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass

    def get_results_csv(
        self,
        subscription_id: str,
        status: Optional[Sequence[Literal["created",
                                          "queued",
                                          "processing",
                                          "failed",
                                          "success"]]] = None
    ) -> Iterator[str]:
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
        results = self._client.get_results_csv(subscription_id, status)
        # Note: retries are not implemented yet. This project has
        # retry logic for HTTP requests, but does not handle errors
        # during streaming. We may want to consider a retry decorator
        # for this entire method a la stamina:
        # https://github.com/hynek/stamina.
        try:
            while True:
                yield self._client._call_sync(results.__anext__())
        except StopAsyncIteration:
            pass
