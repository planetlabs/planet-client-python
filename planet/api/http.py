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
import asyncio
import logging

import httpx

from . import exceptions, models
from . __version__ import __version__

RETRY_COUNT = 5
RETRY_WAIT_TIME = 1  # seconds

LOGGER = logging.getLogger(__name__)


class APlanetSession():
    '''Context manager for asynchronous communication with the Planet server.

    Authentication for Planet servers is given as ('<api key>', '').

    :param auth: Planet server authentication.
    :type auth: httpx.Auth or tuple.
    '''

    def __init__(self, auth=None):
        self._client = httpx.AsyncClient(auth=auth)
        self._client.headers.update({'User-Agent': self._get_user_agent()})
        self._client.event_hooks['request'] = [self._log_request]
        self._client.event_hooks['response'] = [
            self._log_response,
            self._raise_for_status
        ]
        self.retry_wait_time = RETRY_WAIT_TIME
        self.retry_count = RETRY_COUNT

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()

    async def retry(self, func, *a, **kw):
        '''Run an asynchronous request function with retry.'''
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
        raise Exception('too many throttles, giving up')

    async def request(self, request, stream=False):
        '''Submit a request with retry.'''
        # TODO: retry will be provided in httpx v1 [1] with usage [2]
        # 1. https://github.com/encode/httpcore/pull/221
        # 2. https://github.com/encode/httpx/blob/
        # 89fb0cbc69ea07b123dd7b36dc1ed9151c5d398f/docs/async.md#explicit-transport-instances # noqa
        # TODO: if throttling is necessary, check out [1] once v1
        # 1. https://github.com/encode/httpx/issues/984
        return await self.retry(self._request, request, stream=stream)

    async def _request(self, request, stream=False):
        '''Submit a request

        :param request: Request to submit
        :type request: planet.api.models.Request
        :param stream: Get the body as a stream. Defaults to False.
        :type stream: boolean, optional
        :returns: response
        :rtype: planet.api.models.Response
        '''
        http_resp = await self._client.send(request.http_request,
                                            stream=stream)
        return models.Response(request, http_resp)

    def stream(self, request):
        '''Submit a request and get the response as a stream context manager.

        :param request: Request to submit
        :type request: planet.api.models.Request
        :returns: Context manager providing the body as a stream.
        :rtype: APlanetStream
        '''
        return APlanetStream(
            session=self,
            request=request
        )

    @staticmethod
    def _get_user_agent():
        return 'planet-client-python/' + __version__

    @staticmethod
    async def _log_request(request):
        LOGGER.info(f'{request.method} {request.url} - Sent')

    @staticmethod
    async def _log_response(response):
        request = response.request
        LOGGER.info(
            f'{request.method} {request.url} - '
            f'Status {response.status_code}')

    @staticmethod
    async def _raise_for_status(response):
        # TODO: consider using http_response.reason_phrase
        status = response.status_code

        if status < 300:
            return

        exception = {
            400: exceptions.BadQuery,
            401: exceptions.InvalidAPIKey,
            403: exceptions.NoPermission,
            404: exceptions.MissingResource,
            429: exceptions.TooManyRequests,
            500: exceptions.ServerError
        }.get(status, None)

        try:
            msg = response.text
        except httpx.ResponseNotRead:
            await response.aread()
            msg = response.text

        # differentiate between over quota and rate-limiting
        if status == 429 and 'quota' in msg.lower():
            exception = exceptions.OverQuota

        if exception:
            raise exception(msg)

        raise exceptions.APIException(f'{status}: {msg}')


class APlanetStream():
    '''Context manager for asynchronous response stream from Planet server.

    :param session: Open session to Planet server
    :type session: APlanetSession
    :param request: Request to submit
    :type request: planet.api.models.Request
    '''
    def __init__(self, session, request):
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
