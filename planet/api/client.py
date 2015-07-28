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

from .dispatch import RequestsDispatcher
from . import auth
from . import models


class Client(object):


    def __init__(self, api_key=None, base_url='https://api.planet.com/v0/',
                 workers=4):
        api_key = api_key or auth.find_api_key()
        self.auth = api_key and auth.APIKey(api_key)
        self.base_url = base_url
        self.dispatcher = RequestsDispatcher(workers)

    def _request(self, path, body_type=models.JSON, params=None):
        if path.startswith('http'):
            url = path
        else:
            url = self.base_url + path
        return models.Request(url, self.auth, params, body_type)

    def _get(self, path, body_type=models.JSON, params=None, callback=None):
        request = self._request(path, body_type, params)
        response = self.dispatcher.response(request)
        if callback:
            response.get_body_async(callback)
        return response

    def _download_many(self, paths, params, callback):
        return [self._get(path, params=params, callback=callback)
                for path in paths]

    def get_scenes_list(self, scene_type='ortho', order_by=None, count=None,
                        intersects=None, **filters):
        params = {
            'order_by': order_by,
            'count': count,
            'intersects': intersects
        }
        params.update(**filters)
        return self._get('scenes/%s' % scene_type,
                         models.Scenes, params=params).get_body()

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
