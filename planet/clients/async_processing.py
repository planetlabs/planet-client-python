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
"""Planet Async Processing API Python client."""

import asyncio
import logging
import time
from typing import Callable, Dict, Optional

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError, MissingResource
from planet.http import Session

# Async Processing is served per deployment. Data must come from the same
# deployment the request is sent to.
DEPLOYMENT_URLS: Dict[str, str] = {
    'aws-eu-central-1': 'https://services.sentinel-hub.com/async/v1',
    'aws-us-west-2': 'https://services-uswest2.sentinel-hub.com/async/v1',
}
DEFAULT_DEPLOYMENT = 'aws-eu-central-1'

LOGGER = logging.getLogger(__name__)


class AsyncProcessingClient(_BaseClient):
    """Asynchronous Async Processing API client.

    The Async Processing API runs large Process API requests in the
    background and writes the results to your S3 or GCS bucket.

    Authenticate with an OAuth2 user or M2M session (`planet auth login`).
    Planet API keys are not accepted by this API.

    For more information, see
    https://docs.planet.com/develop/apis/async-processing/

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('async_processing')
        ...         # use client here
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None,
                 *,
                 deployment: str = DEFAULT_DEPLOYMENT) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: Custom base URL. Overrides `deployment`.
            deployment: Deployment to send requests to: `aws-eu-central-1`
                (Frankfurt) or `aws-us-west-2` (Oregon). Input data must
                be hosted on the same deployment, and request IDs are only
                known to the deployment that created them.

        Raises:
            planet.exceptions.ClientError: If deployment is unknown.
        """
        if deployment not in DEPLOYMENT_URLS:
            raise ClientError(
                f'Unknown deployment {deployment!r}. Expected one of '
                f'{", ".join(DEPLOYMENT_URLS)}.')
        super().__init__(session, base_url or DEPLOYMENT_URLS[deployment])
        self._process_url = f'{self._base_url}/process'

    async def create_request(self, request: dict) -> dict:
        """Submit an async processing request.

        Malformed requests are raised here. Other errors, including bucket
        access errors, may only appear during processing. These are written
        to `error.json` in the delivery bucket, so a successful submit does
        not mean the request will succeed.

        Parameters:
            request: The request body. See
                [planet.async_processing_request.build_request][].

        Returns:
            dict: `id` and `status` of the submitted request.

        Raises:
            planet.exceptions.APIError: On API error, including
                `TooManyRequests` when the concurrent request limit is
                reached.
        """
        try:
            resp = await self._session.request(method='POST',
                                               url=self._process_url,
                                               json=request)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def get_request(self, request_id: str) -> dict:
        """Get the status of a running request.

        The API reports only running requests. Once a request finishes,
        successfully or not, this raises `MissingResource`. Check the
        delivery bucket for results or `error.json`.

        Parameters:
            request_id: ID of the request.

        Returns:
            dict: `id` and `status` of the request.

        Raises:
            planet.exceptions.MissingResource: If the request has finished
                or does not exist.
            planet.exceptions.APIError: On other API errors.
            planet.exceptions.ClientError: If request_id is empty.
        """
        if not request_id:
            raise ClientError('Must provide a request id.')

        url = f'{self._process_url}/{request_id}'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def wait(self,
                   request_id: str,
                   delay: int = 10,
                   max_attempts: int = 360,
                   callback: Optional[Callable[[str], None]] = None) -> None:
        """Wait until a request is no longer running.

        Polls the request status every `delay` seconds until the API stops
        reporting it. The API cannot tell a finished request from an unknown
        ID, so an ID that never existed also returns at once. Completion
        does not mean success: check the delivery bucket for results or
        `error.json`.

        Parameters:
            request_id: ID of the request.
            delay: Seconds between polls.
            max_attempts: Maximum number of polls. Set to zero for no limit.
            callback: Called with the status after each poll that finds the
                request running.

        Raises:
            planet.exceptions.APIError: On API error.
            planet.exceptions.ClientError: If request_id is empty or
                max_attempts is reached while the request is running.
        """
        num_attempts = 0
        while not max_attempts or num_attempts < max_attempts:
            t = time.time()
            try:
                status = (await self.get_request(request_id))['status']
            except MissingResource:
                LOGGER.debug(f'{request_id} is no longer running')
                return

            LOGGER.debug(status)
            if callback:
                callback(status)

            num_attempts += 1
            await asyncio.sleep(max(delay - (time.time() - t), 0))

        raise ClientError(
            f'Maximum number of attempts ({max_attempts}) reached. '
            f'Request {request_id} is still running.')


__all__ = ['AsyncProcessingClient']
