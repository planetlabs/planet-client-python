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
import os

import httpx
from tqdm.asyncio import tqdm

# from ._fatomic import atomic_open
from . import exceptions, utils


CHUNK_SIZE = 32 * 1024

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


# from contextlib import asynccontextmanager
# class ProgressReporter():
#     def __init__(self):
#         pass
#
#     @asynccontextmanager
#     async def log():
#         yield self
#
#     @staticmethod
#     @asynccontextmanager
#     async def bar(total, filename):
#         yield tqdm(total=total, unit_scale=True,
#                    unit_divisor=1024, unit='B', desc=filename)


    # def get_raw(self):
    #     '''Get the decoded text content from the response'''
    #     return self.response.content.decode('utf-8')
    #
    # def _write(self, fp, callback):
    #     total = 0
    #     if not callback:
    #         def noop(*a, **kw):
    #             pass
    #         callback = noop
    #     callback(start=self)
    #     for chunk in self:
    #         if self._cancel:
    #             raise exceptions.RequestCancelled()
    #         fp.write(chunk)
    #         size = len(chunk)
    #         total += size
    #         callback(wrote=size, total=total)
    #     # seems some responses don't have a content-length header
    #     if self.size == 0:
    #         self.size = total
    #     callback(finish=self)
    #
    # def write(self, file=None, callback=None):
    #     '''Write the contents of the body to the optionally provided file and
    #     providing progress to the optional callback. The callback will be
    #     invoked 3 different ways:
    #
    #     * First as ``callback(start=self)``
    #     * For each chunk of data written as
    #       ``callback(wrote=chunk_size_in_bytes, total=all_byte_cnt)``
    #     * Upon completion as ``callback(finish=self)``
    #
    #     :param file: path or file-like object to write to, defaults to the
    #         name of body
    #     :type file: str or file-like object
    #     :param callback: A function handle of the form
    #         ``callback(start, wrote, total, finish, skip)`` that receives write
    #         progress. Defaults to None
    #     :type callback: function, optional
    #     '''
    #     if not file:
    #         file = self.name
    #     if not file:
    #         raise ValueError('no file name provided or discovered in response')
    #     if hasattr(file, 'write'):
    #         self._write(file, callback)
    #     else:
    #         with atomic_open(file, 'wb') as fp:
    #             self._write(fp, callback)
    #
    # def write_to_file(self, filename=None, overwrite=True, callback=None):
    #     '''Write the contents of the body to the optionally provided filename.
    #
    #     providing progress to the optional callback. The callback will be
    #     invoked 3 different ways:
    #
    #     * First as ``callback(start=self)``
    #     * For each chunk of data written as
    #       ``callback(wrote=chunk_size_in_bytes, total=all_byte_cnt)``
    #     * Upon completion as ``callback(finish=self)`
    #     * Upon skip as `callback(skip=self)`
    #
    #     :param filename: Filename to write to, defaults to body name
    #     :type filename: str, optional
    #     :param overwrite: Specify whether the file at filename
    #         should be overwritten if it exists, defaults to True
    #     :type overwrite: bool, optional
    #     :param callback: A function handle of the form
    #         ``callback(start, wrote, total, finish, skip)`` that receives write
    #         progress. Defaults to None
    #     :type callback: function, optional
    #     '''
    #     if overwrite or not os.path.exists(filename):
    #         self.write(filename, callback=callback)
    #     else:
    #         if callback:
    #             callback(skip=self)


# class JSON(Body):
#     '''A Body that contains JSON'''
#
#     @property
#     def data(self):
#         '''The response as a JSON dict'''
#         data = self.response.json()
#         return data
