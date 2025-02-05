"""Planet Quota Reservations API Python client."""

import logging
from typing import Dict, Optional, TypeVar, Union
from ..http import Session

from planet.exceptions import APIError, ClientError
from ..constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/account/v1/'

LOGGER = logging.getLogger()

T = TypeVar("T")


class QuotaClient:
    """A Planet Quota API client.

    The methods of this class forward request parameters to the
    operations described in the Planet Quota API
    (https://api.planet.com/account/v1/quota-reservations/spec) using HTTP 1.1.

    The methods generally return or yield Python dicts with the same
    structure as the JSON messages used by the service API. Many of the
    exceptions raised by this class are categorized by HTTP client
    (4xx) or server (5xx) errors. This client's level of abstraction is
    low.

    High-level asynchronous access to Planet's quota API:

    Example:
        ```python
        >>> import asyncio
        >>> from planet.clients.quota import QuotaClient
        >>>
        >>> async def main():
        ...     client = QuotaClient(api_key='your_api_key')
        ...     reservations = await client.get_reservations(limit=10)
        ...     print("Reservations:", reservations)
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production orders API
                base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    async def get_my_products(
            self,
            organization_id: Optional[int] = None,
            quota_style: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            sort: Optional[str] = None,
            fields: Optional[str] = None,
            filters: Optional[Dict[str, str]] = None) -> dict:
        """Get a list of available products.

        Args:
            limit (int, optional): Limit parameter for paging output.
            offset (int, optional): Offset parameter for paging output.
            sort (str, optional): Sort specification.
            fields (str, optional): List of comma separated model fields to return only.
            filters (dict, optional): Dictionary of filters to apply.

        Returns:
            dict: A dictionary containing the list of available products.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params: Dict[str, Union[str, int]] = {}
        if organization_id is not None:
            params['organization_id'] = organization_id
        if quota_style is not None:
            params['quota_style'] = quota_style
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if sort is not None:
            params['sort'] = sort
        if fields is not None:
            params['fields'] = fields
        if filters is not None:
            params.update(filters)

        url = f'{self._base_url}/my/products'

        repsonse = await self._session.request('GET', url, params=params)

        return repsonse.json()

    async def estimate_reservation(self, request: dict) -> dict:
        """Estimate a Quota Reservation.

        Args:
            request (dict): quota reservation estimate.

        Returns:
            dict: quota reservation estimate.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """

        url = f'{self._base_url}/quota-reservations/estimate'

        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            return resp.json()

    async def create_reservation(self, request: dict) -> dict:
        """Create a Quota Reservation.

        Args:
            request (dict): quota reservation.

        Returns:
            dict: description of created quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """

        url = f'{self._base_url}/quota-reservations/'

        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            return resp.json()

    async def get_reservations(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            sort: Optional[str] = None,
            fields: Optional[str] = None,
            filters: Optional[Dict[str, str]] = None) -> dict:
        """Get a list of Quota Reservations.

        Args:
            limit (int, optional): Limit parameter for paging output.
            offset (int, optional): Offset parameter for paging output.
            sort (str, optional): Sort specification.
            fields (str, optional): List of comma separated model fields to return only.
            filters (dict, optional): Dictionary of filters to apply.

        Returns:
            dict: A dictionary containing the list of quota reservations.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params: Dict[str, Union[str, int]] = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if sort is not None:
            params['sort'] = sort
        if fields is not None:
            params['fields'] = fields
        if filters is not None:
            params.update(filters)

        url = f'{self._base_url}/quota-reservations/'

        response = await self._session.request('GET', url, params=params)

        return response.json()

    async def get_reservation(self, reservation_id: int) -> dict:
        """Get a description of a Quota Reservation.

        Args:
            reservation_id (int): id of a quota reservation.

        Returns:
            dict: description of the quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/quota-reservations/{reservation_id}'

        response = await self._session.request('GET', url)

        return response.json()

    async def create_bulk_reservations(self, request: dict) -> dict:
        """Create Quota Reservations asynchronously.

        Args:
            request (dict): bulk quota reservation.

        Returns:
            dict: job details of a bulk quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """

        url = f'{self._base_url}/quota-reservations/bulk-reserve'

        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            return resp.json()

    async def get_bulk_reservation_job(self, job_id: int) -> dict:
        """Get a description of a bulk quota reservation job.

        Args:
            reservation_id (int): id of a bulk quota reservation job.

        Returns:
            dict: description of the quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/quota-reservations/jobs/{job_id}'

        repsonse = await self._session.request('GET', url)

        return repsonse.json()
