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
import mimetypes
from pathlib import Path
import random
import re
import string
from typing import AsyncGenerator, Callable, List, Optional
from urllib.parse import urlparse

import httpx
from tqdm.asyncio import tqdm

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


class StreamingResponse(Response):

    @property
    def headers(self) -> httpx.Headers:
        return self._http_response.headers

    @property
    def url(self) -> str:
        return str(self._http_response.url)

    @property
    def num_bytes_downloaded(self) -> int:
        return self._http_response.num_bytes_downloaded

    async def aiter_bytes(self):
        async for c in self._http_response.aiter_bytes():
            yield c

    async def aclose(self):
        await self._http_response.aclose()


class StreamingBody:
    """A representation of a streaming resource from the API."""

    def __init__(self, response: StreamingResponse):
        """Initialize the object.

        Parameters:
            response: Response that was received from the server.
        """
        self._response = response

    @property
    def name(self) -> str:
        """The name of this resource.

        The default is to use the content-disposition header value from the
        response. If not found, falls back to resolving the name from the url
        or generating a random name with the type from the response.
        """
        name = (_get_filename_from_headers(self._response.headers)
                or _get_filename_from_url(self._response.url)
                or _get_random_filename(
                    self._response.headers.get('content-type')))
        return name

    @property
    def size(self) -> int:
        """The size of the body."""
        return int(self._response.headers['Content-Length'])

    async def write(self,
                    filename: Path,
                    overwrite: bool = True,
                    progress_bar: bool = True):
        """Write the body to a file.
        Parameters:
            filename: Name to assign to downloaded file.
            overwrite: Overwrite any existing files.
            progress_bar: Show progress bar during download.
        """

        class _LOG:

            def __init__(self, total, unit, filename, disable):
                self.total = total
                self.unit = unit
                self.disable = disable
                self.previous = 0
                self.filename = str(filename)

                if not self.disable:
                    LOGGER.debug(f'writing to {self.filename}')

            def update(self, new):
                if new - self.previous > self.unit and not self.disable:
                    # LOGGER.debug(f'{new-self.previous}')
                    perc = int(100 * new / self.total)
                    LOGGER.debug(f'{self.filename}: '
                                 f'wrote {perc}% of {self.total}')
                    self.previous = new

        unit = 1024 * 1024

        mode = 'wb' if overwrite else 'xb'
        try:
            with open(filename, mode) as fp:
                _log = _LOG(self.size,
                            16 * unit,
                            filename,
                            disable=progress_bar)
                with tqdm(total=self.size,
                          unit_scale=True,
                          unit_divisor=unit,
                          unit='B',
                          desc=str(filename),
                          disable=not progress_bar) as progress:
                    previous = self._response.num_bytes_downloaded
                    async for chunk in self._response.aiter_bytes():
                        fp.write(chunk)
                        new = self._response.num_bytes_downloaded
                        _log.update(new)
                        progress.update(new - previous)
                        previous = new
        except FileExistsError:
            LOGGER.info(f'File {filename} exists, not overwriting')


def _get_filename_from_headers(headers):
    """Get a filename from the Content-Disposition header, if available.

    :param headers dict: a ``dict`` of response headers
    :returns: a filename (i.e. ``basename``)
    :rtype: str or None
    """
    cd = headers.get('content-disposition', '')
    match = re.search('filename="?([^"]+)"?', cd)
    return match.group(1) if match else None


def _get_filename_from_url(url: str) -> Optional[str]:
    """Get a filename from a url.

    Getting a name for Landsat imagery uses this function.
    """
    path = urlparse(url).path
    name = path[path.rfind('/') + 1:]
    return name or None


def _get_random_filename(content_type=None):
    """Get a pseudo-random, Planet-looking filename.

    :returns: a filename (i.e. ``basename``)
    :rtype: str
    """
    extension = mimetypes.guess_extension(content_type or '') or ''
    characters = string.ascii_letters + '0123456789'
    letters = ''.join(random.sample(characters, 8))
    name = 'planet-{}{}'.format(letters, extension)
    return name


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
