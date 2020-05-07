from .. import auth
from ..client import BASE_URL
from ..exceptions import APIException

import requests
from requests.adapters import HTTPAdapter


class BasemapsClientV1(object):
    def __init__(self, api_key=None, base_url=BASE_URL):
        '''
        :param str api_key: planet API key. Defaults to the PL_API_KEY env var.
        :param str base_url: The base URL to use. Not required.
        '''
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        self.api_key = api_key or auth.find_api_key()
        session = requests.Session()
        session.auth = (self.api_key, '')
        adapter = HTTPAdapter(max_retries=5)
        session.mount("https://", adapter)
        self.session = session

    def _get(self, url):
        resp = self.session.get(url)
        if not resp.ok:
            raise APIException('{}: {}'.format(resp.status_code, resp.content))
        return resp

    def list_basemap_series(self):
        url = self.base_url + 'basemaps/v1/series/'
        while url:
            resp = self._get(url)
            series_list = resp.json().get('series', [])
            for s in series_list:
                yield s
            url = resp.json().get('_links', {}).get('_next')

    def get_basemap_series(self, series_id):
        url = self.base_url + 'basemaps/v1/series/{}'.format(series_id)
        return self._get(url).json()

    def list_mosaics_in_basemap_series(self, series_id):
        url = self.base_url + 'basemaps/v1/series/{}/mosaics'.format(series_id)
        while url:
            resp = self._get(url)
            series_list = resp.json().get('mosaics', [])
            for s in series_list:
                yield s
            url = resp.json().get('_links', {}).get('_next')

    def get_mosaic(self, mosaic_id):
        url = self.base_url + 'basemaps/v1/mosaics/{}'.format(mosaic_id)
        return self._get(url).json()

    def list_quads_in_mosaic(
        self,
        mosaic_id,
        min_lat=-85,
        min_lon=-180,
        max_lat=85,
        max_lon=180
    ):
        bbox = '{},{},{},{}'.format(min_lon, min_lat, max_lon, max_lat)
        url = self.base_url + 'basemaps/v1/mosaics/{}/quads'.format(mosaic_id)
        url += '?bbox={}'.format(bbox)
        while url:
            resp = self._get(url)
            quad_list = resp.json().get('items', [])
            for s in quad_list:
                yield s
            url = resp.json().get('_links', {}).get('_next')
