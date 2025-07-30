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
from typing import Any, Dict, Optional, TypeVar

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError
from planet.http import Session
from ..constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/destinations/v1/'

LOGGER = logging.getLogger()

T = TypeVar("T")


class DestinationsClient(_BaseClient):
    """Asynchronous Destinations API client.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('destinations')
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
            base_url: The base URL to use. Defaults to production destinations
                API base url.
        """
        super().__init__(session, base_url or BASE_URL)

    async def list_destinations(self,
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
        params: Dict[str, Any] = {}
        if archived is not None:
            params["archived"] = archived
        if is_owner is not None:
            params["is_owner"] = is_owner
        if can_write is not None:
            params["can_write"] = can_write

        try:
            response = await self._session.request(method='GET',
                                                   url=self._base_url,
                                                   params=params)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            dest_response = response.json()
            return dest_response

    async def get_destination(self, destination_id: str) -> Dict:
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
        url = f'{self._base_url}/{destination_id}'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            dest = response.json()
            return dest

    async def patch_destination(self,
                                destination_id: str,
                                request: Dict[str, Any]) -> Dict:
        """
        Update a specific destination by its ID.

        Args:
            destination_id (str): The ID of the destination to update.
            request (dict): Destination content to update, only attributes to update are required.

        Returns:
            dict: A dictionary containing the updated destination details.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        url = f'{self._base_url}/{destination_id}'
        try:
            response = await self._session.request(method='PATCH',
                                                   url=url,
                                                   json=request)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            dest = response.json()
            return dest

    async def create_destination(self, request: Dict[str, Any]) -> Dict:
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
        try:
            response = await self._session.request(method='POST',
                                                   url=self._base_url,
                                                   json=request)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            dest = response.json()
            return dest
