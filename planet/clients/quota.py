# Copyright 2026 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Planet Quota Reservations API Python client."""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError
from planet.http import Session
from planet.models import Paged, Response
from ..constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/account/v1'

LOGGER = logging.getLogger()


class _QuotaPaged(Paged):
    """Pager for Quota API list responses.

    Quota API list responses have the shape:
        {"meta": {"count": N, "next": "<url>", "prev": "<url>"}, "results": [...]}
    """
    ITEMS_KEY = 'results'

    def _next_link(self, page):
        try:
            next_link = page['meta']['next']
        except KeyError:
            next_link = False
        if not next_link:
            LOGGER.debug('end of the pages')
        return next_link or False


class QuotaClient(_BaseClient):
    """Asynchronous Quota Reservations API client.

    The methods of this class forward request parameters to the operations
    described in the Planet Quota Reservations API
    (https://api.planet.com/account/v1/quota-reservations/spec).

    For more information, see the documentation at
    https://docs.planet.com/develop/apis/quota/

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('quota')
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
            base_url: The base URL to use. Defaults to the production Account
                API base URL at api.planet.com (`/account/v1`).
        """
        super().__init__(session, base_url or BASE_URL)
        self._reservations_url = f'{self._base_url}/quota-reservations'
        self._products_url = f'{self._base_url}/my/products'

    @staticmethod
    def _filter_params(
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a query-string params dict shared by list endpoints.

        The Quota API accepts `fields`, `sort`, and arbitrary `{field}__{op}` /
        `{field}` filter pairs as query parameters.
        """
        params: Dict[str, Any] = {}
        if fields is not None:
            params['fields'] = fields
        if sort is not None:
            params['sort'] = sort
        if filters:
            params.update(filters)
        return params

    async def list_reservations(
        self,
        limit: int = 100,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 500,
    ) -> AsyncIterator[dict]:
        """Iterate over quota reservations.

        Parameters:
            limit: Maximum number of reservations to return. When set to 0,
                no maximum is applied.
            fields: Comma-separated list of model fields to return.
            sort: Sort spec - `<field>` for ascending or `-<field>` for
                descending.
            filters: Mapping of arbitrary filter parameters. Keys may be
                `{field}` (equality) or `{field}__{op}` where `op` is one of
                `eq`, `lt`, `lte`, `gt`, `gte`, `ne`, `like`, `ilike`,
                `icontains`, `isnull`, `in`, `notin`.
            page_size: Number of results to fetch per page.

        Yields:
            dict: A description of a quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = self._filter_params(fields=fields, sort=sort, filters=filters)
        params['limit'] = page_size

        url = f'{self._reservations_url}/'
        try:
            response = await self._session.request(method='GET',
                                                   url=url,
                                                   params=params)
            async for item in _QuotaPaged(response,
                                          self._session.request,
                                          limit=limit):
                yield item
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def get_reservation(self, reservation_id: int) -> dict:
        """Get a single quota reservation by ID.

        Parameters:
            reservation_id: ID of the quota reservation.

        Returns:
            dict: description of the quota reservation.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._reservations_url}/{reservation_id}'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def create_reservation(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> dict:
        """Create one or more quota reservations.

        Parameters:
            aoi_refs: List of AOI feature references (e.g.
                `pl:features/my/collection-id/feature-id`). Supplying a
                collection ref will reserve every feature in that collection.
            product_id: The product ID from `/my/products`.
            collection_id: Optional grouping collection for the reservation.

        Returns:
            dict: a `QuotaReservationCreated` payload including
                `quota_total`, `quota_used`, `quota_remaining`, and a list of
                created reservation refs.

        Raises:
            APIError: on an API server error (e.g. insufficient quota).
            ClientError: on a client error.
        """
        body: Dict[str, Any] = {
            'aoi_refs': list(aoi_refs),
            'product_id': product_id,
        }
        if collection_id is not None:
            body['collection_id'] = collection_id

        url = f'{self._reservations_url}/'
        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=body)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def bulk_create_reservations(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> dict:
        """Create quota reservations asynchronously via a bulk job.

        Use this endpoint for large batches of AOI references. The response
        includes a `job_id` whose progress can be tracked with
        [planet.clients.quota.QuotaClient.get_job][].

        Parameters:
            aoi_refs: List of AOI feature references.
            product_id: The product ID from `/my/products`.
            collection_id: Optional grouping collection for the reservation.

        Returns:
            dict: payload with `job_id` and `status`.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        body: Dict[str, Any] = {
            'aoi_refs': list(aoi_refs),
            'product_id': product_id,
        }
        if collection_id is not None:
            body['collection_id'] = collection_id

        url = f'{self._reservations_url}/bulk-reserve'
        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=body)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def estimate_reservation(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> dict:
        """Estimate the quota cost of a reservation without creating it.

        To verify there is sufficient quota for the reservation, compare the
        returned `total_cost` against `quota_remaining` - the remaining value
        does not pre-subtract the estimate.

        Parameters:
            aoi_refs: List of AOI feature references.
            product_id: The product ID from `/my/products`.
            collection_id: Optional grouping collection for the reservation.

        Returns:
            dict: a `QuotaReservationEstimation` payload including
                `total_cost`, `estimated_costs`, `quota_total`,
                `quota_remaining`, and `quota_units`.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        body: Dict[str, Any] = {
            'aoi_refs': list(aoi_refs),
            'product_id': product_id,
        }
        if collection_id is not None:
            body['collection_id'] = collection_id

        url = f'{self._reservations_url}/estimate'
        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=body)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def list_jobs(
        self,
        limit: int = 100,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 500,
    ) -> AsyncIterator[dict]:
        """Iterate over bulk quota reservation jobs.

        Parameters:
            limit: Maximum number of jobs to return. When set to 0, no
                maximum is applied.
            fields: Comma-separated list of model fields to return.
            sort: Sort spec - `<field>` for ascending or `-<field>` for
                descending.
            filters: Mapping of `{field}` / `{field}__{op}` filter pairs.
            page_size: Number of results to fetch per page.

        Yields:
            dict: A description of a quota reservation job.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = self._filter_params(fields=fields, sort=sort, filters=filters)
        params['limit'] = page_size

        url = f'{self._reservations_url}/jobs'
        try:
            response = await self._session.request(method='GET',
                                                   url=url,
                                                   params=params)
            async for item in _QuotaPaged(response,
                                          self._session.request,
                                          limit=limit):
                yield item
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def get_job(self, job_id: str) -> dict:
        """Get the status of a bulk reservation job.

        Parameters:
            job_id: ID of the bulk reservation job.

        Returns:
            dict: description of the job, including `status`,
                `processed_items`, `total_items`, and `percentage`.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        if not job_id:
            raise ClientError("Must provide a job id")

        url = f'{self._reservations_url}/jobs/{job_id}'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def list_products(
        self,
        supports_reservation: Optional[bool] = None,
    ) -> List[dict]:
        """List products available to the requesting user's organization.

        Use this to look up the `product_id` (the `id` field) to pass into
        [planet.clients.quota.QuotaClient.create_reservation][],
        [planet.clients.quota.QuotaClient.bulk_create_reservations][],
        or [planet.clients.quota.QuotaClient.estimate_reservation][].

        Parameters:
            supports_reservation: If True, only return products with
                `supports_reservation: true`. If False, only return products
                without reservation support. If None (default), return all
                accessible products.

        Returns:
            list[dict]: products in the user's organization.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        try:
            resp: Response = await self._session.request(
                method='GET', url=self._products_url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

        payload = resp.json()
        # /my/products returns either a list or a dict wrapping a list under
        # a 'results' / 'products' key; tolerate both shapes.
        if isinstance(payload, dict):
            products = payload.get('results') or payload.get('products') or []
        else:
            products = payload

        if supports_reservation is None:
            return list(products)
        return [
            p for p in products
            if bool(p.get('supports_reservation')) == supports_reservation
        ]


__all__ = ['QuotaClient']
