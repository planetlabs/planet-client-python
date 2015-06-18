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

from requests import Session
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
    status = response.status_code
    if status == 200:
        return
    exc = {
        400: BadQuery,
        401: InvalidAPIKey,
        403: NoPermission,
        404: MissingResource,
        429: OverQuota,
        500: ServerError
    }.get(status, None)
    if exc:
        raise exc(response.content)
    raise APIException('%s: %s' % (status, response.content))


def _get_filename(response):
    cd = response.headers.get('content-disposition', '')
    match = re.search('filename="?([^"]+)"?', cd)
    if match:
        return match.group(1)


def _find_api_key():
    return os.getenv(ENV_KEY)


def write_to_file(directory=None, callback=None):
    def writer(session, response):
        _check_status(response)
        img = Image(response)
        file = os.path.join(directory, img.name) if directory else None
        img.write(file, callback)
    return writer


def strp_timestamp(value):
    return datetime.strptime(value, _ISO_FMT)


def strf_timestamp(when):
    return datetime.strftime(when, _ISO_FMT)


class Response(object):

    def __init__(self, response):

        self.response = response
        self.size = int(self.response.headers.get('content-length', -1))
        self.name = _get_filename(self.response)

    def __len__(self):
        return self.size

    def __iter__(self):
        return (chunk for chunk in self.response.iter_content(chunk_size=8192))

    def last_modified(self):
        lm = self.response.headers['last-modified']
        return datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT')

    def get_raw(self):
        return self.response.content


class JSON(Response):

    def get(self):
        return self.response.json()


class Scenes(JSON):

    def __init__(self, response, client):
        super(Scenes, self).__init__(response)
        self._client = client

    def next(self):
        links = self.get()['links']
        next = links.get('next', None)
        if next:
            response = self._client._get(next)
            return Scenes(response, self._client)

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


class Image(Response):

    def _write(self, fp, callback):
        if not callback:
            callback = lambda x: None
        for chunk in self:
            fp.write(chunk)
            callback(len(chunk))
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


class Client(object):


    def __init__(self, api_key=None, base_url='https://api.planet.com/v0/'):
        
        self.api_key = api_key or _find_api_key()
        self.base_url = base_url
        self._workers = 4
        
        headers = {
            'Authorization': 'api-key %s' % self.api_key
        }
        
        # Prepare session and future session objects once
        self.futureSession = FuturesSession(max_workers=self._workers)
        self.futureSession.headers.update(headers)
        
        self.session = Session()
        self.session.headers.update(headers)


    def _get(self, path, params=None, stream=False, callback=None):
        
        if not self.api_key:
            raise InvalidAPIKey('No API key provided')
        
        if path.startswith('http'):
            url = path
        else:
            url = self.base_url + path
        
        if callback:
            r = self.futureSession.get(url, params=params, stream=True, background_callback=callback)
        else:
            r = self.session.get(url, params=params, stream=stream)
            _check_status(r)
        
        return r


    def _get_many(self, paths, params, callback=None):
        return [
            self._get(path, params=params, callback=callback) for path in paths
        ]

    def list_scene_types(self):
        return JSON(self._get('scenes'))

    def get_scenes_list(self, scene_type='ortho', order_by=None, count=None,
                        intersects=None, **filters):
        params = {
            'order_by': order_by,
            'count': count,
            'intersects': intersects
        }
        params.update(**filters)
        return Scenes(self._get('scenes/%s' % scene_type, params=params), self)


    def get_scene_metadata(self, scene_id, scene_type='ortho'):
        """
        Get metadata for a given scene.

        .. todo:: Generalize to accept multiple scene ids.
        """
        return JSON(self._get('scenes/%s/%s' % (scene_type, scene_id)))


    def fetch_scene_geotiffs(self, scene_ids, scene_type='ortho',
                             product='visual', callback=None):
        params = {
            'product': product
        }
        paths = ['scenes/%s/%s/full' % (scene_type, sid) for sid in scene_ids]
        return self._get_many(paths, params, callback)

    def fetch_scene_thumbnails(self, scene_ids, scene_type='ortho', size='md',
                               fmt='png', callback=None):
        params = {
            'size': size,
            'format': fmt
        }
        paths = ['scenes/%s/%s/thumb' % (scene_type, sid) for sid in scene_ids]
        return self._get_many(paths, params, callback)
