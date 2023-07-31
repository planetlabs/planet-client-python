# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
"""Functionality to perform HTTP requests"""
from __future__ import annotations  # https://stackoverflow.com/a/33533514
import asyncio
from collections import Counter
from contextlib import asynccontextmanager
from http import HTTPStatus
import logging
import random
import time
from typing import AsyncGenerator, Optional

import httpx
from typing_extensions import Literal

from .auth import Auth, AuthType
from . import exceptions, models
from .__version__ import __version__

# NOTE: configuration of the session was performed using the data API quick
# search endpoint. These values can be re-tested, tested with a new endpoint or
# refined using session_configuration.py in the scripts directory.

# For how this list was determined, see
# https://github.com/planetlabs/planet-client-python/issues/580
RETRY_EXCEPTIONS = [
    httpx.ConnectError,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    exceptions.BadGateway,
    exceptions.TooManyRequests
]
MAX_RETRIES = 5
MAX_RETRY_BACKOFF = 64  # seconds

# For how these settings were determined, see
# https://github.com/planetlabs/planet-client-python/issues/580
READ_TIMEOUT = 30.0
RATE_LIMIT = 10  # per second
MAX_ACTIVE = 50

LOGGER = logging.getLogger(__name__)


class BaseSession:

    @staticmethod
    def _get_user_agent():
        return 'planet-client-python/' + __version__

    @staticmethod
    def _log_request(request):
        request_pre = f'{request.method} {request.url}'
        LOGGER.info(f'{request_pre} - Sent')
        LOGGER.debug(f'{request_pre} - {request.headers}')
        request.read()
        LOGGER.debug(f'{request_pre} - {request.content}')

    @staticmethod
    def _log_response(response):
        request = response.request
        LOGGER.info(f'{request.method} {request.url} - '
                    f'Status {response.status_code}')
        LOGGER.debug(response.headers)

    @classmethod
    def _convert_and_raise(cls, error):
        response = error.response

        error_types = {
            HTTPStatus.BAD_REQUEST: exceptions.BadQuery,
            HTTPStatus.UNAUTHORIZED: exceptions.InvalidAPIKey,
            HTTPStatus.FORBIDDEN: exceptions.NoPermission,
            HTTPStatus.NOT_FOUND: exceptions.MissingResource,
            HTTPStatus.CONFLICT: exceptions.Conflict,
            HTTPStatus.TOO_MANY_REQUESTS: exceptions.TooManyRequests,
            HTTPStatus.INTERNAL_SERVER_ERROR: exceptions.ServerError,
            HTTPStatus.BAD_GATEWAY: exceptions.BadGateway
        }
        error_type = error_types.get(response.status_code, exceptions.APIError)
        raise error_type(response.text)

    @classmethod
    def _raise_for_status(cls, response):
        if response.is_error:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                e.response.read()
                cls._convert_and_raise(e)

        return


class _Limiter:
    """Limit number of workers and rate of requests.

    Avoids clobbering the API with thousands of async requests.

    Setting rate_limit to zero disables rate (cadence) limiting.
    Setting max_workers to zero disables capping maximum workers.

    This is inspired by asyncio-throttle[1] but altered to enforce cadence
    based on finding that the API returns TooManyRequestError if 2 calls are
    made too close to eachother (even though max rate limit is 5 calls per
    second)[2].

    In investigating options, aiolimiter[3] was also looked at but it seems to
    have odd behavior with httpx [4].

    References:
    [1] https://github.com/hallazzang/asyncio-throttle
    [2] https://github.com/planetlabs/planet-client-python/issues/580#issuecomment-1182752851 # noqa: E501
    [3] https://github.com/mjpieters/aiolimiter
    [4] https://github.com/mjpieters/aiolimiter/issues/73

    The behavior of limiting in communication with live servers can be tested
    and refined using session_configuration.py in the scripts directory.
    """

    def __init__(self, rate_limit=0, max_workers=0):
        # Configuration
        if rate_limit > 0:
            self.cadence = 1.0 / rate_limit
            LOGGER.debug(f'Throttling cadence set to {self.cadence}s.')
        else:
            self.cadence = 0

        self.limit = max_workers
        if self.limit:
            LOGGER.debug(f'Workers capped at {self.limit}.')

        self.retry_interval = 0.01

        # track state
        self._running = 0
        self._last_call = None

    @staticmethod
    def _get_now():
        return time.monotonic()

    async def throttle(self):
        if self.cadence:
            while True:
                now = self._get_now()
                if self._last_call is None:
                    # first call, no need to throttle
                    self._last_call = now
                    break
                elif now - self._last_call >= self.cadence:
                    LOGGER.debug(
                        f'Throught throttle, delta: {now - self._last_call}')
                    self._last_call = now
                    break
                await asyncio.sleep(self.retry_interval)

    async def acquire(self):
        if self.limit:
            while True:
                if self._running < self.limit:
                    self._running += 1
                    LOGGER.debug('Worker acquired.')
                    break
                await asyncio.sleep(self.retry_interval)

    def release(self):
        if self.limit and self._running:
            LOGGER.debug('Worker released.')
            self._running -= 1

    async def __aenter__(self):
        await self.acquire()
        await self.throttle()

    async def __aexit__(self, exc_type, exc, tb):
        self.release()


class Session(BaseSession):
    """Context manager for asynchronous communication with the Planet service.

    The default behavior is to read authentication information stored in the
    secret file. This behavior can be overridden by providing an `auth.Auth`
    instance as an argument.

    Example:
    ```python
    >>> import asyncio
    >>> from planet import Session
    >>>
    >>> async def main():
    ...     async with Session() as sess:
    ...         # communicate with services here
    ...         pass
    ...
    >>> asyncio.run(main())

    ```

    Example:
    ```python
    >>> import async
    >>> from planet import Auth, Session
    >>>
    >>> async def main():
    ...     auth = Auth.from_key('examplekey')
    ...     async with Session(auth=auth) as sess:
    ...         # communicate with services here
    ...         pass
    ...
    >>> asyncio.run(main())

    ```
    """

    def __init__(self, auth: Optional[AuthType] = None):
        """Initialize a Session.

        Parameters:
            auth: Planet server authentication.
        """
        if auth is None:
            # Try getting credentials from environment before checking
            # in the secret file, this is the conventional order (AWS
            # CLI, for example.)
            try:
                auth = Auth.from_env()
            except exceptions.PlanetError:
                auth = Auth.from_file()

        LOGGER.info(f'Session read timeout set to {READ_TIMEOUT}.')
        timeout = httpx.Timeout(10.0, read=READ_TIMEOUT)

        headers = {
            'User-Agent': self._get_user_agent(), 'X-Planet-App': 'python-sdk'
        }

        self._client = httpx.AsyncClient(auth=auth,
                                         headers=headers,
                                         timeout=timeout,
                                         follow_redirects=True)

        async def alog_request(*args, **kwargs):
            return self._log_request(*args, **kwargs)

        async def alog_response(*args, **kwargs):
            return self._log_response(*args, **kwargs)

        self._client.event_hooks['request'] = [alog_request]
        self._client.event_hooks['response'] = [
            alog_response, self._raise_for_status
        ]

        self.max_retries = MAX_RETRIES
        self.max_retry_backoff = MAX_RETRY_BACKOFF

        self._limiter = _Limiter(rate_limit=RATE_LIMIT, max_workers=MAX_ACTIVE)
        self.outcomes: Counter[str] = Counter()

    @classmethod
    async def _raise_for_status(cls, response):
        if response.is_error:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                await e.response.aread()
                cls._convert_and_raise(e)

        return

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()

    async def _retry(self, func, *a, **kw):
        """Run an asynchronous request function with retry.

        Retry uses exponential backoff

        Raises:
            planet.exceptions.TooManyRequests: When retry limit is exceeded.
        """
        # NOTE: if we need something more fancy, consider the following libs:
        # * https://pypi.org/project/retry/
        # * https://pypi.org/project/retrying/
        # TODO: consider increasing the scope of retryable exceptions, ex:
        # https://github.com/googleapis/python-storage/blob/1dc6d647b86466bf133
        # fe03ec8d76c541e19c632/google/cloud/storage/retry.py#L23-L30
        # TODO: if throttling is necessary, check out [1] once v1
        # 1. https://github.com/encode/httpx/issues/984
        num_tries = 0
        while True:
            num_tries += 1
            try:
                resp = await func(*a, **kw)
                break
            except Exception as e:
                if type(e) in RETRY_EXCEPTIONS:
                    if num_tries > self.max_retries:
                        raise e
                    else:
                        self.outcomes.update([type(e)])
                        LOGGER.info(f'Try {num_tries}')
                        LOGGER.info(f'Retrying: caught {type(e)}: {e}')
                        wait_time = self._calculate_wait(
                            num_tries, self.max_retry_backoff)
                        LOGGER.info(f'Retrying: sleeping {wait_time}s')
                        await asyncio.sleep(wait_time)
                else:
                    raise e

        self.outcomes.update(['Successful'])
        return resp

    @staticmethod
    def _calculate_wait(num_tries, max_retry_backoff):
        """Calculates retry wait

        Base wait period is calculated as a exponential based on the number of
        tries. Then, a random jitter of up to 999ms is added to the base wait
        to avoid waves of requests in the case of multiple requests. Finally,
        the wait is thresholded to the maximum retry backoff.

        Because threshold is applied after jitter, calculations that hit
        threshold will not have random jitter applied, they will simply result
        in the threshold value being returned.

        Ref:
        * https://developers.planet.com/docs/data/api-mechanics/
        * https://cloud.google.com/iot/docs/how-tos/exponential-backoff
        """
        random_number_milliseconds = random.randint(0, 999) / 1000.0
        calc_wait = 2**num_tries + random_number_milliseconds
        return min(calc_wait, max_retry_backoff)

    async def request(self,
                      method: str,
                      url: str,
                      json: Optional[dict] = None,
                      params: Optional[dict] = None) -> models.Response:
        """Build a request and submit it with retry and limiting.

        Parameters:
            method: HTTP request method.
            url: Location of the API endpoint.
            json: JSON to send.
            params: Values to send in the query string.

        Returns:
            Server response.

        Raises:
            planet.exceptions.APIException: On API error.
            planet.exceptions.ClientError: When retry limit is exceeded.
        """
        if json:
            headers = {'Content-Type': 'application/json'}
        else:
            headers = None

        request = self._client.build_request(method=method,
                                             url=url,
                                             json=json,
                                             params=params,
                                             headers=headers)

        http_response = await self._retry(self._send, request, stream=False)
        return models.Response(http_response)

    async def _send(self, request, stream=False) -> httpx.Response:
        """Send request with with rate/worker limiting."""
        async with self._limiter:
            http_resp = await self._client.send(request, stream=stream)

        return http_resp

    @asynccontextmanager
    async def stream(
            self, method: str,
            url: str) -> AsyncGenerator[models.StreamingResponse, None]:
        """Submit a request and get the response as a stream context manager.

        Parameters:
            method: HTTP request method.
            url: Location of the API endpoint.

        Returns:
            Context manager providing the streaming response.
        """
        request = self._client.build_request(method=method, url=url)
        http_response = await self._retry(self._send, request, stream=True)
        response = models.StreamingResponse(http_response)
        try:
            yield response
        finally:
            await response.aclose()

    def client(self,
               name: Literal['data', 'orders', 'subscriptions'],
               base_url: Optional[str] = None) -> object:
        """Get a client by its module name.

        Parameters:
            name: one of 'data', 'orders', or 'subscriptions'.

        Returns:
            A client instance.

        Raises:
            ClientError when no such client can be had.

        """
        # To avoid circular dependency.
        from planet.clients import _client_directory

        try:
            return _client_directory[name](self, base_url=base_url)
        except KeyError:
            raise exceptions.ClientError("No such client.")


class AuthSession(BaseSession):
    """Synchronous connection to the Planet Auth service."""

    def __init__(self):
        """Initialize an AuthSession.
        """
        self._client = httpx.Client(timeout=None)
        self._client.headers.update({'User-Agent': self._get_user_agent()})
        self._client.event_hooks['request'] = [self._log_request]
        self._client.event_hooks['response'] = [
            self._log_response, self._raise_for_status
        ]

    def request(self, method: str, url: str, json: dict):
        """Submit a request

        Parameters:
            method: HTTP request method.
            url: Location of the API endpoint.
            json: JSON to send.

        Returns:
            Server response.

        Raises:
            planet.exceptions.APIException: On API error.
        """
        request = self._client.build_request(method=method, url=url, json=json)
        http_resp = self._client.send(request)
        return models.Response(http_resp)

    @classmethod
    def _raise_for_status(cls, response):
        try:
            super()._raise_for_status(response)
        except exceptions.BadQuery:
            raise exceptions.APIError('Not a valid email address.')
        except exceptions.InvalidAPIKey:
            raise exceptions.APIError('Incorrect email or password.')
