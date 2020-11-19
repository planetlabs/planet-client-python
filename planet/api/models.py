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

from ._fatomic import atomic_open
from .exceptions import InvalidAPIKey, RequestCancelled
from . import utils


CHUNK_SIZE = 32 * 1024

LOGGER = logging.getLogger(__name__)


class Request(object):
    def __init__(self, url, auth, params=None, body_type=None, data=None,
                 method='GET'):
        self.url = url
        self.auth = auth
        self.params = params

        body_type = body_type or Order
        LOGGER.debug('Request body type: {}'.format(body_type))
        assert issubclass(body_type, Body)
        self.body_type = body_type

        self.data = data
        self.method = method

    @property
    def headers(self):
        headers = {}
        if self.data:
            headers['Content-Type'] = 'application/json'

        # TODO: change this to try/except
        if self.auth:
            headers.update({
                'Authorization': 'api-key %s' % self.auth.value
            })
        else:
            raise InvalidAPIKey('No API key provided')
        return headers


class Response(object):
    def __init__(self, request, http_response):
        self.request = request
        self.http_response = http_response
        self._body = None

    @property
    def body(self):
        '''The response Body

        :returns Body: A Body object containing the response.
        '''
        if self._body is None:
            self._body = self._create_body()
        return self._body

    def _create_body(self):
        return self.request.body_type(self.request, self.http_response)


class Body(object):
    '''A Body is a representation of a resource from the API.
    '''

    def __init__(self, request, http_response):
        self._request = request
        self.response = http_response
        self.size = int(self.response.headers.get('content-length', 0))
        self._cancel = False

    @property
    def name(self):
        '''The name of this resource. The default is to use the
        content-disposition header value from the response.'''
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
                raise RequestCancelled()
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

        :param file: file name or file-like object
        :param callback: optional progress callback
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


class JSON(Body):
    '''A Body that contains JSON'''

    def get(self):
        '''Get the response as a JSON dict'''
        return self.response.json()


class Order(JSON):
    LINKS_KEY = '_links'
    RESULTS_KEY = 'results'
    LOCATION_KEY = 'location'

    @property
    def results(self):
        links = self.get()[self.LINKS_KEY]
        results = links.get(self.RESULTS_KEY, None)
        return results

    @property
    def items(self):
        results = self.results()
        locations = [r[self.LOCATION_KEY] for r in results]
        return locations

    @property
    def items_iter(self):
        '''An iterator of the 'items' in each order.
        The iterator yields the individual items in the order.

        :return: iter of items in order
        '''
        # TODO: maybe this should be like items
        # but a generator?
        locations = iter(self.locations())
        return locations

    @property
    def state(self):
        return self.get()['state']
