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

from ._fatomic import atomic_open
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
    :param auth: Planet API authentication
    :type auth: :py:Class:'planet.auth.auth
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
    def __init__(self, url, auth, params=None, body_type=None, data=None,
                 method='GET'):
        self.url = url
        self.auth = auth
        self.params = params

        self.body_type = body_type or Body
        if not issubclass(self.body_type, Body):
            raise RequestException(
                f'body_type ({self.body_type}) must be a subclass of Body'
            )

        self.data = data
        self.method = method

    @property
    def headers(self):
        '''Prepare headers for request.

        :returns: prepared headers
        :rtype: dict
        '''
        headers = {}
        if self.data:
            headers['Content-Type'] = 'application/json'

        if self.auth:
            headers.update({
                'Authorization': 'api-key %s' % self.auth.value
            })
        else:
            raise exceptions.InvalidAPIKey('No API key provided')
        return headers


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
        self._body = None

    @property
    def body(self):
        '''The response Body

        :returns: A Body object containing the response
        :rtype: :py:Class:`Body`
        '''
        if self._body is None:
            self._body = self._create_body()
        return self._body

    def _create_body(self):
        return self.request.body_type(self.request, self.http_response)

    @property
    def status_code(self):
        '''HTTP status code.

        :returns: status code
        :rtype: int
        '''
        return self.http_response.status_code

    def __repr__(self):
        return '<models.Response [%s]>' % (self.status_code)

    def raise_for_status(self):
        '''Raises :class: `APIException` if one occured.'''
        return self._raise_for_status(self.status_code, self.http_response)

    @staticmethod
    def _raise_for_status(status, http_response):
        LOGGER.debug(f'status code: {status}')

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

        # differentiate between over quota and rate-limiting
        res = http_response
        if status == 429 and 'quota' in res.text.lower():
            exception = exceptions.OverQuota

        if exception:
            raise exception(res.text)

        raise exceptions.APIException('%s: %s' % (status, res.text))


class Body():
    '''A Body is a representation of a resource from the API.

    :param request: Request that was submitted to the server
    :type request: :py:Class:`planet.api.models.Request
    :param http_response: Response that was received from the server
    :type http_response: :py:Class:`requests.models.Response`
        '''
    def __init__(self, request, http_response):
        self._request = request
        self.response = http_response

        self.size = int(self.response.headers.get('content-length', 0))
        self._cancel = False

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

    def __len__(self):
        return self.size

    def __iter__(self):
        return (c for c in self.response.iter_content(chunk_size=CHUNK_SIZE))

    def last_modified(self):
        '''Read the last-modified header as a datetime, if present.'''
        lm = self.response.headers.get('last-modified', None)
        return datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT') if lm \
            else None

    def get_raw(self):
        '''Get the decoded text content from the response'''
        return self.response.content.decode('utf-8')

    def _write(self, fp, callback):
        total = 0
        if not callback:
            def noop(*a, **kw):
                pass
            callback = noop
        callback(start=self)
        for chunk in self:
            if self._cancel:
                raise exceptions.RequestCancelled()
            fp.write(chunk)
            size = len(chunk)
            total += size
            callback(wrote=size, total=total)
        # seems some responses don't have a content-length header
        if self.size == 0:
            self.size = total
        callback(finish=self)

    def write(self, file=None, callback=None):
        '''Write the contents of the body to the optionally provided file and
        providing progress to the optional callback. The callback will be
        invoked 3 different ways:

        * First as ``callback(start=self)``
        * For each chunk of data written as
          ``callback(wrote=chunk_size_in_bytes, total=all_byte_cnt)``
        * Upon completion as ``callback(finish=self)``

        :param file: path or file-like object to write to, defaults to the
            name of body
        :type file: str or file-like object
        :param callback: A function handle of the form
            ``callback(start, wrote, total, finish, skip)`` that receives write
            progress. Defaults to None
        :type callback: function, optional
        '''
        if not file:
            file = self.name
        if not file:
            raise ValueError('no file name provided or discovered in response')
        if hasattr(file, 'write'):
            self._write(file, callback)
        else:
            with atomic_open(file, 'wb') as fp:
                self._write(fp, callback)

    def write_to_file(self, filename=None, overwrite=True, callback=None):
        '''Write the contents of the body to the optionally provided filename.

        providing progress to the optional callback. The callback will be
        invoked 3 different ways:

        * First as ``callback(start=self)``
        * For each chunk of data written as
          ``callback(wrote=chunk_size_in_bytes, total=all_byte_cnt)``
        * Upon completion as ``callback(finish=self)`
        * Upon skip as `callback(skip=self)`

        :param filename: Filename to write to, defaults to body name
        :type filename: str, optional
        :param overwrite: Specify whether the file at filename
            should be overwritten if it exists, defaults to True
        :type overwrite: bool, optional
        :param callback: A function handle of the form
            ``callback(start, wrote, total, finish, skip)`` that receives write
            progress. Defaults to None
        :type callback: function, optional
        '''
        if overwrite or not os.path.exists(filename):
            self.write(filename, callback=callback)
        else:
            if callback:
                callback(skip=self)


class JSON(Body):
    '''A Body that contains JSON'''

    @property
    def data(self):
        '''The response as a JSON dict'''
        data = self.response.json()
        return data
