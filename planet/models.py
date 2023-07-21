# Copyright 2015 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Manage data for requests and responses."""
import logging
from typing import AsyncGenerator, Callable, List

import httpx

from .exceptions import PagingError

LOGGER = logging.getLogger(__name__)


class Response:
    """Handles the Planet server's response to a HTTP request."""

    def __init__(self, http_response: httpx.Response):
        """Initialize object.

        Parameters:
            http_response: Response that was received from the server.
        """
        self._http_response = http_response

    def __repr__(self):
        return f'<models.Response [{self.status_code}]>'

    @property
    def status_code(self) -> int:
        """HTTP status code"""
        return self._http_response.status_code

    def json(self) -> dict:
        """Response json"""
        return self._http_response.json()


class Paged:
    """Asynchronous iterator over results in a paged resource.

    Each returned result is a JSON dict.
    """
    LINKS_KEY = '_links'
    NEXT_KEY = 'next'
    ITEMS_KEY = 'items'

    def __init__(self,
                 response: Response,
                 request_fcn: Callable,
                 limit: int = 0):
        """
        Parameters:
            request: Request to send to server for first page.
            request_fcn: Function for submitting a request and retrieving a
            result. Must take in url and method parameters.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.
        """
        self._request_fcn = request_fcn

        self._pages = self._get_pages(response)

        self._items: List[dict] = []

        self.i = 0
        self.limit = limit

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict:
        # This was implemented because traversing _get_pages()
        # in an async generator was resulting in retrieving all the
        # pages, when the goal is to stop retrieval when the limit
        # is reached
        if self.limit and self.i >= self.limit:
            raise StopAsyncIteration

        try:
            item = self._items.pop(0)
            self.i += 1
        except IndexError:
            page = await self._pages.__anext__()
            self._items = page[self.ITEMS_KEY]
            try:
                item = self._items.pop(0)
                self.i += 1
            except IndexError:
                raise StopAsyncIteration

        return item

    async def _get_pages(self, response) -> AsyncGenerator:
        page = response.json()
        yield page

        next_url = self._next_link(page)
        while (next_url):
            LOGGER.debug('getting next page')
            response = await self._request_fcn(url=next_url, method='GET')
            page = response.json()

            # If the next URL is the same as the previous URL we will
            # get the same response and be stuck in a page cycle. This
            # has happened in development and could happen in the case
            # of a bug in the production API.
            prev_url = next_url
            next_url = self._next_link(page)

            if next_url == prev_url:
                raise PagingError(
                    "Page cycle detected at {!r}".format(next_url))

            yield page

    def _next_link(self, page):
        try:
            next_link = page[self.LINKS_KEY][self.NEXT_KEY]
            LOGGER.debug(f'next: {next_link}')
        except KeyError:
            LOGGER.debug('end of the pages')
            next_link = False
        return next_link
