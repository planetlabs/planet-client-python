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

import base64
import json
from .dispatch import RequestsDispatcher
from . import auth
from .exceptions import (InvalidIdentity, APIException)
from . import models
from .utils import check_status


class Client(object):
    '''High-level access to Planet's API.'''
    def __init__(self, api_key=None, base_url='https://api.planet.com/v0/',
                 workers=4):
        '''
        :param str api_key: API key to use. Defaults to environment variable.
        :param str base_url: The base URL to use. Not required.
        :param int workers: The number of concurrent download workers
        '''
        api_key = api_key or auth.find_api_key()
        self.auth = api_key and auth.APIKey(api_key)
        self.base_url = base_url
        self.dispatcher = RequestsDispatcher(workers)

    def shutdown(self):
        self.dispatcher.session.executor.shutdown(wait=False)

    def _url(self, path):
        if path.startswith('http'):
            url = path
        else:
            url = self.base_url + path
        return url

    def _request(self, path, body_type=models.JSON, params=None, auth=None):
        return models.Request(self._url(path), auth or self.auth, params,
                              body_type)

    def _get(self, path, body_type=models.JSON, params=None, callback=None):
        # convert any JSON objects to text explicitly
        for k, v in (params or {}).items():
            if isinstance(v, dict):
                params[k] = json.dumps(v)

        request = self._request(path, body_type, params)
        response = self.dispatcher.response(request)
        if callback:
            response.get_body_async(callback)
        return response

    def _download_many(self, paths, params, callback):
        return [self._get(path, models.Image, params=params, callback=callback)
                for path in paths]

    def login(self, identity, credentials):
        '''Login using email identity and credentials. Returns a JSON
        object containing an `api_key` property with the user's API_KEY.
        :param str identity: email
        :param str credentials: password
        :returns: JSON object (Python dict)
        '''
        result = self.dispatcher.session.post(self._url('auth/login'), {
            'email': identity,
            'password': credentials
        }).result()
        status = result.status_code
        if status == 400:
            raise APIException('invalid parameters, login process has changed')
        elif status == 401:
            # do our best to get something out to the user
            msg = result.text
            try:
                msg = json.loads(result.text)['message']
            finally:
                raise InvalidIdentity(msg)
        elif status != 200:
            raise APIException('%s: %s' % (status, result.text))
        jwt = result.text
        payload = jwt.split('.')[1]
        rem = len(payload) % 4
        if rem > 0:
            payload += '=' * (4 - rem)
        payload = base64.urlsafe_b64decode(payload.encode('utf-8'))
        return json.loads(payload.decode('utf-8'))

    def get_scenes_list(self, scene_type='ortho', order_by=None, count=None,
                        intersects=None, workspace=None, **filters):
        '''Get scenes matching the specified parameters and filters.

        :param str scene_type: The type of scene, defaults to 'ortho'
        :param str order_by: Results order 'acquired asc' or 'acquired desc'.
           Defaults to 'acquired desc'
        :param int count: Number of results per page. Defaults to 50.
        :param intersects: A geometry to filter results by. Can be one of:
           WKT or GeoJSON text or a GeoJSON-like dict.
        :param filters: Zero or more metadata filters in the form of
           param.name.comparison -> value.
        :returns: :py:class:`Scenes` body
        '''
        params = {
            'order_by': order_by,
            'count': count,
            'intersects': intersects
        }
        if workspace:
            params['workspace'] = workspace
        params.update(**filters)
        return self._get('scenes/%s/' % scene_type,
                         models.Scenes, params=params).get_body()

    def get_scene_metadata(self, scene_id, scene_type='ortho'):
        """
        Get metadata for a given scene.

        :param str scene_id: The scene ID
        :param str scene_type: The type: either 'ortho' or 'landsat'
        :return: :py:class:`JSON` body
        """
        # todo: accept/return multiple scenes
        return self._get('scenes/%s/%s' % (scene_type, scene_id)).get_body()

    def fetch_scene_geotiffs(self, scene_ids, scene_type='ortho',
                             product='visual', callback=None):
        """
        Download scene geotiffs. The provided callback will be called with a
        single argument, the :py:class:`Body` object, when the response is
        ready and successful (it will be initiated with response headers).

        :param sequence scene_ids: The scene IDs to download
        :param str scene_type: The type: either 'ortho' or 'landsat'
        :param str product: The product type, varies on scene_type.
        :param function callback: A callback for handling asynchronous results
        :return: a sequence of :py:class:`Response` objects, one for each scene
           id provided
        """
        params = {
            'product': product
        }
        paths = ['scenes/%s/%s/full' % (scene_type, id) for id in scene_ids]
        return self._download_many(paths, params, callback)

    def fetch_scene_thumbnails(self, scene_ids, scene_type='ortho', size='md',
                               fmt='png', callback=None):
        """
        Download scene thumbnails. The provided callback will be called with a
        single argument, the :py:class:`Body` object, when the response is
        ready and successful (it will be initiated with response headers).

        :param sequence scene_ids: The scene IDs to download
        :param str scene_type: The type: either 'ortho' or 'landsat'
        :param str size: The size: 'sm', 'md', 'lg'
        :param str format: The image format: 'png', 'jpg'
        :param function callback: A callback for handling asynchronous results
        :return: a sequence of :py:class:`Response` objects, one for each scene
           id provided
        """
        params = {
            'size': size,
            'format': fmt
        }
        paths = ['scenes/%s/%s/thumb' % (scene_type, id) for id in scene_ids]
        return self._download_many(paths, params, callback)

    def list_mosaics(self):
        """
        List all mosaics.
        """
        return self._get('mosaics/', models.Mosaics).get_body()

    def get_mosaic(self, name):
        """
        Get metadata for a given mosaic.

        :param name:
            Mosaic name as returned by `list_mosaics`.
        """
        return self._get('mosaics/%s' % name).get_body()

    def get_mosaic_quads(self, name, intersects=None, count=50):
        """
        Get metadata for mosaic quads.

        :param name:
            Mosaic name as retured by `list_mosaics`.
        :param intersects:
            WKT or GeoJSON describing a region of interest.
        :param count:
            Number of results to return.
        """

        params = {}
        if intersects:
            params['intersects'] = intersects
        if count:
            params['count'] = count
        path = 'mosaics/%s/quads/' % name
        return self._get(path, models.Quads, params).get_body()

    def fetch_mosaic_quad_geotiffs(self, mosaic_name, quad_ids, callback=None):
        pt = 'mosaics/%s/quads/%s/full'
        paths = [pt % (mosaic_name, qid) for qid in quad_ids]
        return self._download_many(paths, {}, callback)

    def get_workspaces(self):
        return self._get('workspaces/').get_body()

    def get_workspace(self, id):
        return self._get('workspaces/%s' % id).get_body()

    def set_workspace(self, workspace, id=None):
        if id:
            workspace['id'] = id
            url = 'workspaces/%s' % id
            method = 'PUT'
        else:
            'id' in workspace and workspace.pop('id')
            url = 'workspaces/'
            method = 'POST'
        # without these, scenes UI breaks
        defaults = {
            "filters": {}
        }
        defaults.update(workspace)
        result = self.dispatcher.dispatch_request(method, self.base_url + url,
                                                  data=json.dumps(defaults),
                                                  auth=self.auth)
        check_status(result)
        return models.JSON(None, result, self.dispatcher)
