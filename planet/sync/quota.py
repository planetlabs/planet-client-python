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
from typing import Iterator, Optional
from planet.clients.quota import QuotaClient
from planet.http import Session


class QuotaAPI:
    """Synchronous quota API wrapper.
    Provides synchronous access to Planet's quota reservation functionality.
    """
    _client: QuotaClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production quota API
                base url.
        """
        self._client = QuotaClient(session, base_url)

    def create_reservation(self, request: dict) -> dict:
        """Create a new quota reservation.
        Parameters:
            request: Quota reservation request specification.
        Returns:
            Description of the created reservation.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(
            self._client.create_reservation(request))

    def estimate_quota(self, request: dict) -> dict:
        """Estimate quota requirements for a potential reservation.
        Parameters:
            request: Quota estimation request specification.
        Returns:
            Quota estimation details including projected costs and usage.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.estimate_quota(request))

    def list_reservations(self,
                          status: Optional[str] = None,
                          limit: int = 100) -> Iterator[dict]:
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
        return self._client._aiter_to_iter(
            self._client.list_reservations(status=status, limit=limit))

    def get_reservation(self, reservation_id: str) -> dict:
        """Get a quota reservation by ID.
        Parameters:
            reservation_id: Quota reservation identifier.
        Returns:
            Quota reservation details.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(
            self._client.get_reservation(reservation_id))

    def cancel_reservation(self, reservation_id: str) -> dict:
        """Cancel an existing quota reservation.
        Parameters:
            reservation_id: Quota reservation identifier.
        Returns:
            Updated reservation details.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(
            self._client.cancel_reservation(reservation_id))

    def get_quota_usage(self) -> dict:
        """Get current quota usage and limits.
        Returns:
            Current quota usage statistics and limits.
        Raises:
            planet.exceptions.APIError: On API error.
        """
        return self._client._call_sync(self._client.get_quota_usage())
