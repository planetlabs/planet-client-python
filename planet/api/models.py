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
from .utils import get_filename
from .utils import check_status
from datetime import datetime

chunk_size = 32 * 1024


class Response(object):

    def __init__(self, request, dispatcher):
        self.request = request
        self._dispatcher = dispatcher
        self._body = None
        self._future = None

    def _create_body(self, response):
        return self.request.body_type(self.request, response, self._dispatcher)

    def get_body(self):
        if self._body is None:
            resp = self._dispatcher._dispatch(self.request)
            self._body = self._create_body(resp)
        return self._body

    def _async_callback(self, session, response):
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
        if self._future:
            self._future.result()
            return self._body


class Request(object):

    def __init__(self, url, auth, params=None, body_type=Response):
        self.url = url
        self.auth = auth
        self.params = params
        self.body_type = body_type


class Body(object):

    def __init__(self, request, http_response, dispatcher):
        self._request = request
        self.response = http_response
        self._dispatcher = dispatcher
        self.size = int(self.response.headers.get('content-length', 0))
        self.name = get_filename(self.response)

    def __len__(self):
        return self.size

    def __iter__(self):
        return (c for c in self.response.iter_content(chunk_size=chunk_size))

    def last_modified(self):
        lm = self.response.headers['last-modified']
        return datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT')

    def get_raw(self):
        return self.response.content.decode('utf-8')

    def _write(self, fp, callback):
        total = 0
        if not callback:
            callback = lambda x: None
        for chunk in self:
            fp.write(chunk)
            size = len(chunk)
            total += size
            callback(size)
        # seems some responses don't have a content-length header
        if self.size is 0:
            self.size = total
        callback(self)

    def write(self, file=None, callback=None):
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

    def get(self):
        return self.response.json()


class Scenes(JSON):

    def next(self):
        links = self.get()['links']
        next = links.get('next', None)
        if next:
            request = Request(next, self._request.auth, body_type=Scenes)
            return self._dispatcher.response(request).get_body()

    def iter(self, pages=None):
        pages = int(10e10) if pages is None else pages
        page = self
        if pages > 0:
            yield page
            pages -= 1
        while pages > 0:
            page = page.next()
            if page is None:
                break
            yield page
            pages -= 1


class Image(Body):
    pass
