# Copyright 2015 Planet Labs, Inc.
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

import datetime
import logging

import httpx
from tqdm.asyncio import tqdm

from . import utils


LOGGER = logging.getLogger(__name__)


class RequestException(Exception):
    """Exceptions thrown by RequestException"""
    pass


class Request():
    '''Handles a HTTP request for the Planet server.

    :param url: URL of API endpoint
    :type url: str
    :param params: values to send in the query string, defaults to None
    :type params: dict, list of tuples, or bytes, optional
    :param body_type: Expected response body type, defaults to `Body`
    :type body_type: type, optional
    :param data: object to send in the body, defaults to None
    :type data: dict, list of tuples, bytes, or file-like object, optional
    :param method: HTTP request method, defaults to 'GET'
    :type method: str, optional
    :raises RequestException: When provided `body_type` is not a subclass of
        :py:class:`planet.api.models.Body`
    '''
    def __init__(self, url, params=None, data=None, method='GET'):
        if data:
            headers = {'Content-Type': 'application/json'}
        else:
            headers = None

        self.http_request = httpx.Request(
            method,
            url,
            params=params,
            data=data,
            headers=headers)


class Response():
    '''Handles the Planet server's response to a HTTP request

    :param request: Request that was submitted to the server
    :type request: :py:Class:`Request`
    :param http_response: Response that was received from the server
    :type http_response: :py:Class:`requests.models.Response`
    '''
    def __init__(self, request, http_response):
        self.request = request
        self.http_response = http_response

    def __repr__(self):
        return f'<models.Response [{self.status_code}]>'

    @property
    def status_code(self):
        '''HTTP status code.

        :returns: status code
        :rtype: int
        '''
        return self.http_response.status_code

    @property
    def json(self):
        return self.http_response.json

    async def aclose(self):
        await self.http_response.aclose()


class StreamingBody():
    '''A representation of a streaming resource from the API.

    :param response: Response that was received from the server
    :type response: :py:Class:`requests.models.Response`
        '''
    def __init__(self, response):
        self.response = response.http_response

    @property
    def name(self):
        '''The name of this resource.

        The default is to use the content-disposition header value from the
        response. If not found, falls back to resolving the name from the url
        or generating a random name with the type from the response.

        :returns: name of this resource
        :rtype: str
        '''
        return utils.get_filename(self.response)

    @property
    def size(self):
        return int(self.response.headers['Content-Length'])

    @property
    def num_bytes_downloaded(self):
        return self.response.num_bytes_downloaded

    def last_modified(self):
        '''Read the last-modified header as a datetime, if present.'''
        lm = self.response.headers.get('last-modified', None)
        return datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT') if lm \
            else None

    async def aiter_bytes(self):
        async for c in self.response.aiter_bytes():
            yield c

    async def write(self, filename, overwrite=True, progress_bar=True):
        class _LOG():
            def __init__(self, total, unit, filename, disable):
                self.total = total
                self.unit = unit
                self.disable = disable
                self.previous = 0
                self.filename = filename

                if not self.disable:
                    LOGGER.debug(f'writing to {self.filename}')

            def update(self, new):
                if new-self.previous > self.unit and not self.disable:
                    # LOGGER.debug(f'{new-self.previous}')
                    perc = int(100 * new / self.total)
                    LOGGER.debug(f'{self.filename}: '
                                 f'wrote {perc}% of {self.total}')
                    self.previous = new

        unit = 1024*1024

        mode = 'wb' if overwrite else 'xb'
        try:
            with open(filename, mode) as fp:
                _log = _LOG(self.size, 16*unit, filename, disable=progress_bar)
                with tqdm(total=self.size, unit_scale=True,
                          unit_divisor=unit, unit='B',
                          desc=filename, disable=not progress_bar) as progress:
                    previous = self.num_bytes_downloaded
                    async for chunk in self.aiter_bytes():
                        fp.write(chunk)
                        new = self.num_bytes_downloaded
                        _log.update(new)
                        progress.update(new-previous)
                        previous = new
        except FileExistsError:
            LOGGER.info(f'File {filename} exists, not overwriting')
