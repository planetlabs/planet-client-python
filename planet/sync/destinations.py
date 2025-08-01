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

from typing import Any, Dict, Optional
from planet.clients.destinations import DestinationsClient
from planet.http import Session


class DestinationsAPI:

    _client: DestinationsClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Destinations API
                base url.
        """

        self._client = DestinationsClient(session, base_url)

    def list_destinations(self,
                          archived: Optional[bool] = None,
                          is_owner: Optional[bool] = None,
                          can_write: Optional[bool] = None) -> Dict:
        """
        List all destinations. By default, all non-archived destinations in the requesting user's org are returned.

        Args:
            archived (bool): If True, include archived destinations.
            is_owner (bool): If True, include only destinations owned by the requesting user.
            can_write (bool): If True, include only destinations the requesting user can modify.

        Returns:
            dict: A dictionary containing the list of destinations inside the 'destinations' key.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.list_destinations(archived, is_owner, can_write))

    def get_destination(self, destination_id: str) -> Dict:
        """
        Get a specific destination by its ID.

        Args:
            destination_id (str): The ID of the destination to retrieve.

        Returns:
            dict: A dictionary containing the destination details.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.get_destination(destination_id))

    def patch_destination(self, destination_ref: str,
                          request: Dict[str, Any]) -> Dict:
        """
        Update a specific destination by its ref.

        Args:
            destination_ref (str): The ref of the destination to update.
            request (dict): Destination content to update, only attributes to update are required.

        Returns:
            dict: A dictionary containing the updated destination details.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.patch_destination(destination_ref, request))

    def create_destination(self, request: Dict[str, Any]) -> Dict:
        """
        Create a new destination.

        Args:
            request (dict): Destination content to create, all attributes are required.

        Returns:
            dict: A dictionary containing the created destination details.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.create_destination(request))
