# Copyright 2020 Planet Labs, Inc.
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
from http import HTTPStatus
import logging

import httpx

from ..auth import Auth
from . import exceptions, models
from . __version__ import __version__

RETRY_COUNT = 5
RETRY_WAIT_TIME = 1  # seconds

LOGGER = logging.getLogger(__name__)


class SessionException(Exception):
    '''exceptions thrown by Session'''
    pass


class BaseSession():
    @staticmethod
    def _get_user_agent():
        return 'planet-client-python/' + __version__

    @staticmethod
    def _log_request(request):
        LOGGER.info(f'{request.method} {request.url} - Sent')

    @staticmethod
    def _log_response(response):
        request = response.request
        LOGGER.info(
            f'{request.method} {request.url} - '
            f'Status {response.status_code}')

    @staticmethod
    def _raise_for_status(response):
        # TODO: consider using http_response.reason_phrase
        status = response.status_code

        miminum_bad_request_code = HTTPStatus.MOVED_PERMANENTLY
        if status < miminum_bad_request_code:
            return

        exception = {
            HTTPStatus.BAD_REQUEST: exceptions.BadQuery,
            HTTPStatus.UNAUTHORIZED: exceptions.InvalidAPIKey,
            HTTPStatus.FORBIDDEN: exceptions.NoPermission,
            HTTPStatus.NOT_FOUND: exceptions.MissingResource,
            HTTPStatus.TOO_MANY_REQUESTS: exceptions.TooManyRequests,
            HTTPStatus.INTERNAL_SERVER_ERROR: exceptions.ServerError
        }.get(status, None)

        msg = response.text

        # differentiate between over quota and rate-limiting
        if status == 429 and 'quota' in msg.lower():
            exception = exceptions.OverQuota

        if exception:
            raise exception(msg)

        raise exceptions.APIException(f'{status}: {msg}')


class Session(BaseSession):
    '''Context manager for asynchronous communication with the Planet service.

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
    '''

    def __init__(
        self,
        auth: Auth = None
    ):
        """Initialize a Session.

        Parameters:
            auth: Planet server authentication.
        """
        auth = auth or Auth.from_file()

        self._client = httpx.AsyncClient(auth=auth)
        self._client.headers.update({'User-Agent': self._get_user_agent()})

        async def alog_request(*args, **kwargs):
            return self._log_request(*args, **kwargs)

        async def alog_response(*args, **kwargs):
            return self._log_response(*args, **kwargs)

        async def araise_for_status(*args, **kwargs):
            return self._raise_for_status(*args, **kwargs)

        self._client.event_hooks['request'] = [alog_request]
        self._client.event_hooks['response'] = [
            alog_response,
            araise_for_status
        ]
        self.retry_wait_time = RETRY_WAIT_TIME
        self.retry_count = RETRY_COUNT

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()

    async def _retry(self, func, *a, **kw):
        '''Run an asynchronous request function with retry.'''
        # TODO: retry will be provided in httpx v1 [1] with usage [2]
        # 1. https://github.com/encode/httpcore/pull/221
        # 2. https://github.com/encode/httpx/blob/
        # 89fb0cbc69ea07b123dd7b36dc1ed9151c5d398f/docs/async.md#explicit-transport-instances # noqa
        # TODO: if throttling is necessary, check out [1] once v1
        # 1. https://github.com/encode/httpx/issues/984
        retry_count = self.retry_count
        wait_time = self.retry_wait_time

        max_retry = retry_count + 1
        for i in range(max_retry):
            try:
                return await func(*a, **kw)
            except exceptions.TooManyRequests:
                if i < max_retry:
                    LOGGER.debug(f'Try {i}')
                    LOGGER.info(f'Too Many Requests: sleeping {wait_time}s')
                    # TODO: consider exponential backoff
                    # https://developers.planet.com/docs/data/api-mechanics/
                    await asyncio.sleep(wait_time)
        raise SessionException('Too many throttles, giving up.')

    async def request(
        self,
        request: models.Request,
        stream: bool = False
    ) -> models.Response:
        '''Submit a request with retry.

        Parameters:
            request: Request to submit.
            stream: Get the body as a stream.
        Returns:
            Response.
        '''
        # TODO: retry will be provided in httpx v1 [1] with usage [2]
        # 1. https://github.com/encode/httpcore/pull/221
        # 2. https://github.com/encode/httpx/blob/
        # 89fb0cbc69ea07b123dd7b36dc1ed9151c5d398f/docs/async.md#explicit-transport-instances # noqa
        # TODO: if throttling is necessary, check out [1] once v1
        # 1. https://github.com/encode/httpx/issues/984
        return await self._retry(self._request, request, stream=stream)

    async def _request(self, request, stream=False):
        '''Submit a request'''
        http_resp = await self._client.send(request.http_request,
                                            stream=stream)
        return models.Response(request, http_resp)

    def stream(
        self,
        request: models.Request
    ) -> Stream:
        '''Submit a request and get the response as a stream context manager.

        Parameters:
            request: Request to submit
        Returns:
            Context manager providing the body as a stream.
        '''
        return Stream(
            session=self,
            request=request
        )


class AuthSession(BaseSession):
    '''Synchronous connection to the Planet Auth service.'''
    def __init__(self):
        """Initialize an AuthSession.
        """
        self._client = httpx.Client(timeout=None)
        self._client.headers.update({'User-Agent': self._get_user_agent()})
        self._client.event_hooks['request'] = [self._log_request]
        self._client.event_hooks['response'] = [
            self._log_response,
            self._raise_for_status
        ]

    def request(self, request):
        '''Submit a request'''
        http_resp = self._client.send(request.http_request)
        return models.Response(request, http_resp)

    @classmethod
    def _raise_for_status(cls, response):
        try:
            super()._raise_for_status(response)
        except exceptions.BadQuery:
            raise exceptions.APIException('Not a valid email address.')
        except exceptions.InvalidAPIKey:
            raise exceptions.APIException('Incorrect email or password.')


class Stream():
    '''Context manager for asynchronous response stream from Planet server.'''
    def __init__(
        self,
        session: Session,
        request: models.Request
    ):
        """
        Parameters:
            session: Open session to Planet server.
            request:  Request to submit.
        """
        self.session = session
        self.request = request

    async def __aenter__(self):
        self.response = await self.session.request(
            request=self.request,
            stream=True,
        )
        return self.response

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        await self.response.aclose()
