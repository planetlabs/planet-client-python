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

from datetime import datetime
import logging
import os
import re

from requests_futures.sessions import FuturesSession

_logger = logging.getLogger(__name__)

ENV_KEY = 'PL_API_KEY'

_ISO_FMT = '%Y-%m-%dT%H:%M:%S.%f+00:00'


class APIException(Exception):
    '''also used as placeholder for unexpected response status_code'''
    pass


class BadQuery(APIException):
    pass


class InvalidAPIKey(APIException):
    pass


class NoPermission(APIException):
    pass


class MissingResource(APIException):
    pass


class OverQuota(APIException):
    pass


class ServerError(APIException):
    pass


def _check_status(response):
    '''check the status of the response and if needed raise an APIException'''
    status = response.status_code
    if status == 200:
        return
    exception = {
        400: BadQuery,
        401: InvalidAPIKey,
        403: NoPermission,
        404: MissingResource,
        429: OverQuota,
        500: ServerError
    }.get(status, None)

    if exception:
        raise exception(response.content)

    raise APIException('%s: %s' % (status, response.content))


def _get_filename(response):
    cd = response.headers.get('content-disposition', '')
    match = re.search('filename="?([^"]+)"?', cd)
    if match:
        return match.group(1)


def _find_api_key():
    return os.getenv(ENV_KEY)


def write_to_file(directory=None, callback=None):
    def writer(body):
        file = os.path.join(directory, body.name) if directory else None
        body.write(file, callback)
    return writer


def strp_timestamp(value):
    return datetime.strptime(value, _ISO_FMT)


def strf_timestamp(when):
    return datetime.strftime(when, _ISO_FMT)


class Response(object):

    def __init__(self, request, dispatcher):
        self.request = request
        self._dispatcher = dispatcher
        self._body = None
        self._future = None

    def _create_body(self, response):
        return self.request.body_type(response, self._dispatcher)

    def get_body(self):
        if self._body is None:
            resp = self._dispatcher._dispatch(self.request)
            self._body = self._create_body(resp)
        return self._body

    def _async_callback(self, session, response):
        _check_status(response)
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

    def __init__(self, url, params=None, body_type=Response):
        self.url = url
        self.params = params
        self.body_type = body_type


class Body(object):

    def __init__(self, http_response, dispatcher):
        self.response = http_response
        self._dispatcher = dispatcher
        self.size = int(self.response.headers.get('content-length', 0))
        self.name = _get_filename(self.response)

    def __len__(self):
        return self.size

    def __iter__(self):
        return (chunk for chunk in self.response.iter_content(chunk_size=8192))

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
        if isinstance(file, basestring):
            with open(file, 'wb') as fp:
                self._write(fp, callback)
        else:
            self._write(file, callback)


class JSON(Body):

    def get(self):
        return self.response.json()


class Scenes(JSON):

    def next(self):
        links = self.get()['links']
        next = links.get('next', None)
        if next:
            request = Request(next, body_type=Scenes)
            return self._dispatcher.response(request).get_body()

    def iter(self, pages=None):
        pages = int(10e10) if pages is None else pages
        page = self
        if pages > 0:
            yield page
            pages -= 1
        while pages > 0:
            page = page.next()
            yield page
            pages -= 1


class Image(Body):
    pass


class Dispatcher(object):

    def __init__(self, api_key, workers=4):
        self.session = FuturesSession(max_workers=workers)
        self.set_api_key(api_key)

    def set_api_key(self, api_key):
        if api_key:
            self.session.headers.update({
                'Authorization': 'api-key %s' % api_key
            })
        elif 'authorization' in self.session.headers:
            self.session.headers.pop('authorization')

    def response(self, request):
        return Response(request, self)

    def _dispatch_async(self, request, callback):
        if not 'authorization' in self.session.headers:
            raise InvalidAPIKey('No API key provided')
        return self.session.get(request.url, params=request.params,
                                stream=True, background_callback=callback)

    def _dispatch(self, request, callback=None):
        response = self._dispatch_async(request, callback).result()
        _check_status(response)
        return response


class Client(object):

    def __init__(self, api_key=None, base_url='https://api.planet.com/v0/',
                 workers=4):
        api_key = api_key or _find_api_key()
        self.base_url = base_url
        self.dispatcher = Dispatcher(api_key, workers)

    def _get(self, path, body_type=JSON, params=None, callback=None):
        if path.startswith('http'):
            url = path
        else:
            url = self.base_url + path
        request = Request(url, params, body_type)
        response = self.dispatcher.response(request)
        if callback:
            response.get_body_async(callback)
        return response

    def _download_many(self, paths, params, callback):
        return [self._get(path, params=params, callback=callback)
                for path in paths]

    def list_scene_types(self):
        return self._get('scenes').get_body()

    def get_scenes_list(self, scene_type='ortho', order_by=None, count=None,
                        intersects=None, **filters):
        params = {
            'order_by': order_by,
            'count': count,
            'intersects': intersects
        }
        params.update(**filters)
        return self._get('scenes/%s' % scene_type,
                         Scenes, params=params).get_body()

    def get_scene_metadata(self, scene_id, scene_type='ortho'):
        """
        Get metadata for a given scene.

        .. todo:: Generalize to accept multiple scene ids.
        """
        return self._get('scenes/%s/%s' % (scene_type, scene_id)).get_body()

    def fetch_scene_geotiffs(self, scene_ids, scene_type='ortho',
                             product='visual', callback=None):
        params = {
            'product': product
        }
        paths = ['scenes/%s/%s/full' % (scene_type, sid) for sid in scene_ids]
        return self._download_many(paths, params, callback)

    def fetch_scene_thumbnails(self, scene_ids, scene_type='ortho', size='md',
                               fmt='png', callback=None):
        params = {
            'size': size,
            'format': fmt
        }
        paths = ['scenes/%s/%s/thumb' % (scene_type, sid) for sid in scene_ids]
        return self._download_many(paths, params, callback)


    def list_mosaics(self):
        """
        List all mosaics.
        
        .. todo:: Pagination
        """
        return self._get('mosaics').get_body()


    def get_mosaic(self, name):
        """
        Get metadata for a given mosaic.
        
        :param name:
            Mosaic name as returned by `list_mosaics`.
        """
        return self._get('mosaics/%s' % name).get_body()

