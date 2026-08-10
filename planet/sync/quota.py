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
"""Synchronous Planet Quota Reservations API client."""

from typing import Any, Dict, Iterator, List, Optional

from planet.clients.quota import QuotaClient
from planet.http import Session


class QuotaAPI:
    """Quota Reservations API client.

    Example:
        ```python
        >>> from planet import Planet
        >>>
        >>> pl = Planet()
        >>> for r in pl.quota.list_reservations():
        ...     print(r)
        ```
    """

    _client: QuotaClient

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to the production Account
                API base URL.
        """
        self._client = QuotaClient(session, base_url)

    def list_reservations(
        self,
        limit: int = 100,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 500,
    ) -> Iterator[dict]:
        """Iterate over quota reservations.

        See [planet.clients.quota.QuotaClient.list_reservations][] for
        parameter details.
        """
        return self._client._aiter_to_iter(
            self._client.list_reservations(limit=limit,
                                           fields=fields,
                                           sort=sort,
                                           filters=filters,
                                           page_size=page_size))

    def get_reservation(self, reservation_id: int) -> Dict[str, Any]:
        """Get a single quota reservation by ID."""
        return self._client._call_sync(
            self._client.get_reservation(reservation_id))

    def create_reservation(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create one or more quota reservations.

        Parameters:
            aoi_refs: List of AOI feature references (e.g.
                `pl:features/my/collection-id/feature-id`).
            product_id: The product ID from `/my/products`.
            collection_id: Optional grouping collection for the reservation.
        """
        return self._client._call_sync(
            self._client.create_reservation(aoi_refs,
                                            product_id,
                                            collection_id))

    def bulk_create_reservations(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a bulk quota reservation job.

        Returns a payload with `job_id` and `status` - track progress with
        [planet.sync.quota.QuotaAPI.get_job][].
        """
        return self._client._call_sync(
            self._client.bulk_create_reservations(aoi_refs,
                                                  product_id,
                                                  collection_id))

    def estimate_reservation(
        self,
        aoi_refs: List[str],
        product_id: int,
        collection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Estimate the quota cost of a reservation without creating it."""
        return self._client._call_sync(
            self._client.estimate_reservation(aoi_refs,
                                              product_id,
                                              collection_id))

    def list_jobs(
        self,
        limit: int = 100,
        fields: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 500,
    ) -> Iterator[dict]:
        """Iterate over bulk quota reservation jobs."""
        return self._client._aiter_to_iter(
            self._client.list_jobs(limit=limit,
                                   fields=fields,
                                   sort=sort,
                                   filters=filters,
                                   page_size=page_size))

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a bulk reservation job."""
        return self._client._call_sync(self._client.get_job(job_id))

    def list_products(
        self,
        supports_reservation: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """List products available to the requesting user's organization.

        Use this to look up the `product_id` (the `id` field) to pass into
        [planet.sync.quota.QuotaAPI.create_reservation][],
        [planet.sync.quota.QuotaAPI.bulk_create_reservations][],
        or [planet.sync.quota.QuotaAPI.estimate_reservation][].

        Parameters:
            supports_reservation: If True, only return products with
                `supports_reservation: true`.
        """
        return self._client._call_sync(
            self._client.list_products(supports_reservation))
