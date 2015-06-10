from datetime import datetime
import os
import re
import requests

ENV_KEY = 'PL_API_KEY'


class APIException(Exception):
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


def check_status(response):
    exc = {
        200: None,
        400: BadQuery,
        401: InvalidAPIKey,
        403: NoPermission,
        404: MissingResource,
        429: OverQuota,
        500: ServerError
    }.get(response.status_code, APIException)
    if exc:
        raise exc(response.content)


def push_params(params, **kv):
    params.update([(k, v) for k, v in kv.items() if v])
    return params


def get_filename(response):
    cd = response.headers['content-disposition']
    match = re.search('filename="?([^"]+)"?', cd)
    if match:
        return match.group(1)
    raise APIException('Unable to locate filename in response: %s' % cd)


def _find_api_key():
    return os.getenv(ENV_KEY)


class Image(object):

    def __init__(self, response):
        self.response = response
        self.size = int(self.response.headers.get('content-length', -1))
        self.name = get_filename(self.response)

    def __len__(self):
        return self.size

    def __iter__(self):
        return (chunk for chunk in self.response.iter_content(chunk_size=8096))

    def last_modified(self):
        lm = self.response.headers['last-modified']
        return datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT')

    def _write(self, fp, callback):
        if not callback:
            callback = lambda x: None
        for chunk in self:
            fp.write(chunk)
            callback(len(chunk))

    def write(self, file=None, callback=None):
        if not file:
            file = self.name
        if isinstance(file, basestring):
            with open(file, 'wb') as fp:
                self._write(fp, callback)
        else:
            self._write(file, callback)


class Client(object):

    def __init__(self, api_key=None, base_url='https://api.planet.com/v0/'):
        self.api_key = api_key or _find_api_key()
        self.base_url = base_url

    def _get(self, path, params=None, stream=False):
        url = self.base_url + path
        headers = {'Authorization': 'api-key ' + self.api_key}
        r = requests.get(url, headers=headers, params=params, stream=stream)
        check_status(r)
        return r

    def list_all_scene_types(self):
        return self._get('scenes').content

    def get_scenes_list(self, scene_type=None, order_by=None, count=None,
                        intersects=None, **filters):
        scene_type = scene_type or 'ortho'
        params = {}
        push_params(params, order_by=order_by, count=count)
        push_params(params, intersects=intersects)
        push_params(params, **filters)
        return self._get('scenes/%s' % scene_type, params=params).content

    def fetch_scene_info(self, scene_id, scene_type=None):
        scene_type = scene_type or 'ortho'
        return self._get('scenes/%s/%s' % (scene_type, scene_id)).content

    def fetch_scene_geotiff(self, scene_id, scene_type=None,
                            product_type=None):
        scene_type = scene_type or 'ortho'
        product_type = product_type or 'visual'
        path = 'scenes/%s/%s/full' % (scene_type, scene_id)
        r = self._get(path, stream=True)
        return Image(r)

    def fetch_scene_thumbnail(self, scene_id, scene_type=None, size=None,
                              format=None):
        scene_type = scene_type or 'ortho'
        size = size or 'lg'
        format = format or 'jpg'
        params = {'size': size, 'format': format}
        path = 'scenes/%s/%s/thumb' % (scene_type, scene_id)
        r = self._get(path, params=params)
        return Image(r)
