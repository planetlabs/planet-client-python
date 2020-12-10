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
from . import exceptions, utils


CHUNK_SIZE = 32 * 1024

LOGGER = logging.getLogger(__name__)


class Request(object):
    '''Handles a HTTP request for the Planet server'''
    def __init__(self, url, auth, params=None, body_type=None, data=None,
                 method='GET'):
        '''
        :param str url: URL of API endpoint
        :param :py:Class:'planet.auth.auth auth: Planet API authentication
        :param dict params (opt): Request parameters
        :param type body_type: Exptected response body type
        :param data: Request body
        :param str method: HTTP request method
        '''
        self.url = url
        self.auth = auth
        self.params = params

        body_type = body_type or Body
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

        if self.auth:
            headers.update({
                'Authorization': 'api-key %s' % self.auth.value
            })
        else:
            raise exceptions.InvalidAPIKey('No API key provided')
        return headers


class Response(object):
    '''Handles the Planet server's response to a HTTP request
    '''
    def __init__(self, request, http_response):
        '''
        :param :py:Class:`Request` request: Request that was
            submitted to the server.
        :param :py:Class:`requests.models.Response` http_response: Response
            that was received from the server.
        '''
        self.request = request
        self.http_response = http_response
        self._body = None

    @property
    def body(self):
        '''The response Body

        :returns :py:Class:`Body`: A Body object containing the response.
        '''
        if self._body is None:
            self._body = self._create_body()
        return self._body

    def _create_body(self):
        return self.request.body_type(self.request, self.http_response)

    @property
    def status_code(self):
        return self.http_response.status_code

    def __repr__(self):
        return '<models.Response [%s]>' % (self.status_code)

    def raise_for_status(self):
        '''Raises :class: `APIException` if one occured.'''
        self._raise_for_status(self.status_code, self.http_response.text)

    @staticmethod
    def _raise_for_status(status, text):
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
        if status == 429 and 'quota' in text.lower():
            exception = exceptions.OverQuota

        if exception:
            raise exception(text)

        raise exceptions.APIException('%s: %s' % (status, text))


class Body(object):
    '''A Body is a representation of a resource from the API.
    '''

    def __init__(self, request, http_response):
        '''
        :param :py:Class:`planet.api.models.Request request: Request that was
            submitted to the server.
        :param :py:Class:'requests.models.Response http_response: Response that
            was received from the server.
        '''
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

    @property
    def data(self):
        data = self.get()
        return data

    def get(self):
        '''Get the response as a JSON dict'''
        return self.response.json()


# class Orders(Paged):
#     def _get_item_key(self):
#         return 'orders'
#
#     def _get_links_key(self):
#         return '_links'
#
#     def _get_next_key(self):
#         return 'next'
#
#
# def _abstract():
#     raise NotImplementedError("You need to override this function")
#
#
# class Paged(JSON):
#     '''A paged response representing multiple results.
#
#     This is meant to be inherited and the following methods overridden:
#         - _get_item_key()
#         - _get_links_key()
#         - _get_next_key()
#     '''
#     def _get_item_key(self):
#         '''Example: return "features"'''
#         _abstract()
#
#     def _get_links_key(self):
#         '''Example: return "_links"'''
#         _abstract()
#
#     def _get_next_key(self):
#         '''Example: return "_next"'''
#         _abstract()
#
#     def next(self):
#         links = self.get()[self._get_links_key()]
#         next_ = links.get(self._get_next_key(), None)
#         if next_:
#             request = Request(next_, self._request.auth,
#                               body_type=type(self))
#             return self._dispatcher.response(request).get_body()
#
#     def _pages(self):
#         page = self
#         while page is not None:
#             yield page
#             page = page.next()
#
#     def iter(self, pages=None):
#         '''Get an iterator of pages.
#
#         :param int pages: optional limit to number of pages
#         :return: iter of this and subsequent pages
#         '''
#         i = self._pages()
#         if pages is not None:
#             i = itertools.islice(i, pages)
#         return i
#
#     def items_iter(self, limit):
#         '''Get an iterator of the 'items' in each page. Instead of a feature
#         collection from each page, the iterator yields the features.
#
#         :param int limit: The number of 'items' to limit to.
#         :return: iter of items in page
#         '''
#
#         pages = (page.get() for page in self._pages())
#         items = itertools.chain.from_iterable(
#             (p[self._get_item_key()] for p in pages)
#         )
#         if limit is not None:
#             items = itertools.islice(items, limit)
#         return items
#
#     def json_encode(self, out, limit=None, sort_keys=False, indent=None):
#         '''Encode the results of this paged response as JSON writing to the
#         provided file-like `out` object. This function will iteratively read
#         as many pages as present, streaming the contents out as JSON.
#
#         :param file-like out: an object with a `write` function
#         :param int limit: optional maximum number of items to write
#         :param bool sort_keys: if True, output keys sorted, default is False
#         :param bool indent: if True, indent output, default is False
#         '''
#         stream = self._json_stream(limit)
#         enc = json.JSONEncoder(indent=indent, sort_keys=sort_keys)
#         for chunk in enc.iterencode(stream):
#             out.write(u'%s' % chunk)
#
#     def _json_stream(self, limit):
#         items = self.get()[self._get_item_key()]
#         # if there are no results, _GeneratorAdapter doesn't play well
#         if len(items):
#             items = _GeneratorAdapter(self.items_iter(limit))
#         else:
#             items = []
#         return {
#             self._get_item_key(): items
#         }
#
#
# class _GeneratorAdapter(list):
#     '''Allow a generator to be used in JSON serialization'''
#     def __init__(self, gen):
#         self.gen = gen
#
#     def __iter__(self):
#         return self.gen
#
#     def __len__(self):
#         return 1
