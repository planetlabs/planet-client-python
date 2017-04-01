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

from ._fatomic import atomic_open
from .exceptions import RequestCancelled
from .utils import get_filename
from .utils import check_status
from .utils import GeneratorAdapter
from datetime import datetime
import itertools
import json

chunk_size = 32 * 1024


class Response(object):

    def __init__(self, request, dispatcher):
        self.request = request
        self._dispatcher = dispatcher
        self._body = None
        self._future = None
        self._cancel = False

    def _create_body(self, response):
        return self.request.body_type(self.request, response, self._dispatcher)

    def get_body(self):
        '''Get the response Body

        :returns Body: A Body object containing the response.
        '''
        if self._body is None:
            resp = self._dispatcher._dispatch(self.request)
            self._body = self._create_body(resp)
        return self._body

    def _async_callback(self, session, response):
        if self._cancel:
            raise RequestCancelled()
        check_status(response)
        self._body = self._create_body(response)
        self._handler(self._body)
        if self._await:
            self._await(self._body)

    def get_body_async(self, handler, await=None):
        if self._future is None:
            self._handler = handler
            self._await = await
            self._future = self._dispatcher._dispatch_async(
                self.request, self._async_callback
            )

    def await(self):
        '''Await completion of this request.

        :returns Body: A Body object containing the response.
        '''
        if self._future:
            self._future.result()
        return self._body

    def cancel(self):
        '''Cancel any request.'''
        if self._body:
            self._body._cancel = True
        else:
            self._cancel = True


class Request(object):

    def __init__(self, url, auth, params=None, body_type=Response, data=None,
                 method='GET'):
        self.url = url
        self.auth = auth
        self.params = params
        self.body_type = body_type
        self.data = data
        self.method = method


class Body(object):
    '''A Body is a representation of a resource from the API.
    '''

    def __init__(self, request, http_response, dispatcher):
        self._request = request
        self.response = http_response
        self._dispatcher = dispatcher
        self.size = int(self.response.headers.get('content-length', 0))
        self._cancel = False

    @property
    def name(self):
        '''The name of this resource. The default is to use the
        content-disposition header value from the response.'''
        return get_filename(self.response)

    def __len__(self):
        return self.size

    def __iter__(self):
        return (c for c in self.response.iter_content(chunk_size=chunk_size))

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
        if self.size is 0:
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


class Paged(JSON):

    ITEM_KEY = 'features'
    LINKS_KEY = '_links'
    NEXT_KEY = '_next'

    def next(self):
        links = self.get()[self.LINKS_KEY]
        next = links.get(self.NEXT_KEY, None)
        if next:
            request = Request(next, self._request.auth, body_type=type(self))
            return self._dispatcher.response(request).get_body()

    def _pages(self):
        page = self
        while page is not None:
            yield page
            page = page.next()

    def iter(self, pages=None):
        '''Get an iterator of pages.

        :param int pages: optional limit to number of pages
        :return: iter of this and subsequent pages
        '''
        i = self._pages()
        if pages is not None:
            i = itertools.islice(i, pages)
        return i

    def json_encode(self, out, limit=None, sort_keys=False, indent=None):
        '''Encode the results of this paged response as JSON writing to the
        provided file-like `out` object. This function will iteratively read
        as many pages as present, streaming the contents out as JSON.

        :param file-like out: an object with a `write` function
        :param int limit: optional maximum number of items to write
        :param bool sort_keys: if True, output keys sorted, default is False
        :param bool indent: if True, indent output, default is False
        '''
        stream = self._json_stream(limit)
        enc = json.JSONEncoder(indent=indent, sort_keys=sort_keys)
        for chunk in enc.iterencode(stream):
            out.write(u'%s' % chunk)

    def items_iter(self, limit):
        '''Get an iterator of the 'items' in each page. Instead of a feature
        collection from each page, the iterator yields the features.

        :param int limit: The number of 'items' to limit to.
        :return: iter of items in page
        '''

        pages = (page.get() for page in self._pages())
        items = itertools.chain.from_iterable(
            (p[self.ITEM_KEY] for p in pages)
        )
        if limit is not None:
            items = itertools.islice(items, limit)
        return items

    def _json_stream(self, limit):
        items = self.get()[self.ITEM_KEY]
        # if there are no results, the GeneratorAdapter doesn't play well
        if len(items):
            items = GeneratorAdapter(self.items_iter(limit))
        else:
            items = []
        return {
            self.ITEM_KEY: items
        }


class Features(Paged):

    def _json_stream(self, limit):
        stream = super(Features, self)._json_stream(limit)
        json_body = self.get()
        # patch back in the count if present
        if 'count' in json_body:
            stream['count'] = json_body.get('count')
        stream['type'] = 'FeatureCollection'
        return stream


class Items(Features):
    pass


class Searches(Paged):
    ITEM_KEY = 'searches'
