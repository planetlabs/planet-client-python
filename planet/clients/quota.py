# Copyright 2025 Planet Labs PBC.
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
import logging
from typing import AsyncIterator, Optional
from planet.clients.base import _BaseClient
from planet.constants import PLANET_BASE_URL
from planet.http import Session
from planet.models import Paged

BASE_URL = f'{PLANET_BASE_URL}/quota/v1'
LOGGER = logging.getLogger(__name__)


class Reservations(Paged):
    """Asynchronous iterator over reservations from a paged response."""
    NEXT_KEY = '_next'
    ITEMS_KEY = 'reservations'


class QuotaClient(_BaseClient):
    """High-level asynchronous access to Planet's quota API.
    The Planet Quota Reservations API allows you to create, estimate, and view
    existing quota reservations on the Planet platform for compatible products
    including Planetary Variables, Analysis-Ready PlanetScope (ARPS), and select
    PlanetScope imagery products.
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

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production quota API
                base url.
        """
        super().__init__(session, base_url or BASE_URL)

    def _reservations_url(self):
        return f'{self._base_url}/reservations'

    async def create_reservation(self, request: dict) -> dict:
        """Create a new quota reservation.
        Parameters:
            request: Quota reservation request specification.
        Returns:
            Description of the created reservation.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._reservations_url()
        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def estimate_quota(self, request: dict) -> dict:
        """Estimate quota requirements for a potential reservation.
        Parameters:
            request: Quota estimation request specification.
        Returns:
            Quota estimation details including projected costs and usage.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/estimate'
        response = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        return response.json()

    async def list_reservations(self,
                                status: Optional[str] = None,
                                limit: int = 100) -> AsyncIterator[dict]:
        """Iterate through list of quota reservations.
        Parameters:
            status: Filter reservations by status (e.g., 'active', 'completed', 'cancelled').
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.
        Yields:
            Description of a quota reservation.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = self._reservations_url()
        params = {}
        if status:
            params['status'] = status
        response = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
        async for reservation in Reservations(response,
                                              self._session.request,
                                              limit=limit):
            yield reservation

    async def get_reservation(self, reservation_id: str) -> dict:
        """Get a quota reservation by ID.
        Parameters:
            reservation_id: Quota reservation identifier.
        Returns:
            Quota reservation details.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._reservations_url()}/{reservation_id}'
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def cancel_reservation(self, reservation_id: str) -> dict:
        """Cancel an existing quota reservation.
        Parameters:
            reservation_id: Quota reservation identifier.
        Returns:
            Updated reservation details.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._reservations_url()}/{reservation_id}/cancel'
        response = await self._session.request(method='POST', url=url)
        return response.json()

    async def get_quota_usage(self) -> dict:
        """Get current quota usage and limits.
        Returns:
            Current quota usage statistics and limits.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        url = f'{self._base_url}/usage'
        response = await self._session.request(method='GET', url=url)
        return response.json()
