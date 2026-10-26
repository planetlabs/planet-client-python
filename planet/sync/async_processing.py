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
"""Synchronous Planet Async Processing API client."""

from typing import Any, Callable, Dict, Optional

from planet.clients.async_processing import (AsyncProcessingClient,
                                             DEFAULT_DEPLOYMENT)
from planet.http import Session


class AsyncProcessingAPI:
    """Async Processing API client.

    Example:
        ```python
        >>> from planet import Planet
        >>>
        >>> pl = Planet()
        >>> req = pl.async_processing.create_request(request)
        >>> pl.async_processing.wait(req['id'])
        ```
    """

    _client: AsyncProcessingClient

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None,
                 *,
                 deployment: str = DEFAULT_DEPLOYMENT) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: Custom base URL. Overrides `deployment`.
            deployment: Deployment to send requests to. See
                [planet.clients.async_processing.AsyncProcessingClient][].
        """
        self._client = AsyncProcessingClient(session,
                                             base_url,
                                             deployment=deployment)

    def create_request(self, request: dict) -> Dict[str, Any]:
        """Submit an async processing request.

        See [planet.clients.async_processing.AsyncProcessingClient.create_request][]
        for details.
        """
        return self._client._call_sync(self._client.create_request(request))

    def get_request(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a running request.

        See [planet.clients.async_processing.AsyncProcessingClient.get_request][]
        for details.
        """
        return self._client._call_sync(self._client.get_request(request_id))

    def wait(self,
             request_id: str,
             delay: int = 10,
             max_attempts: int = 360,
             callback: Optional[Callable[[str], None]] = None) -> None:
        """Wait until a request is no longer running.

        See [planet.clients.async_processing.AsyncProcessingClient.wait][]
        for details.
        """
        return self._client._call_sync(
            self._client.wait(request_id,
                              delay=delay,
                              max_attempts=max_attempts,
                              callback=callback))
