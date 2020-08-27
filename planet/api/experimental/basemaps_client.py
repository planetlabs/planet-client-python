from .. import auth
from ..client import BASE_URL
from ..exceptions import APIException

import os
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

    def _get(self, url, **kwargs):
        resp = self.session.get(url, params=kwargs)
        if not resp.ok:
            raise APIException('{}: {}'.format(resp.status_code, resp.content))
        return resp

    def _post(self, url, body):
        resp = self.session.post(url, json=body)
        if not resp.ok:
            raise APIException('{}: {}'.format(resp.status_code, resp.content))
        return resp

    def list_mosaics(self, name__is=None, name__contains=None):
        url = self.base_url + 'basemaps/v1/mosaics/'
        params = {}
        params['name__is'] = name__is
        params['name__contains'] = name__contains
        resp = self._get(url, name__is=name__is, name__contains=name__contains)
        mosaics = resp.json().get('mosaics', [])
        return mosaics

    def list_mosaic_series(self, name__is=None, name__contains=None):
        url = self.base_url + 'basemaps/v1/series/'
        resp = self._get(url, name__is=name__is, name__contains=name__contains)
        mosaic_series = resp.json()
        return mosaic_series

    def get_mosaic_series(self, series_id):
        url = self.base_url + 'basemaps/v1/series/{}'.format(series_id)
        return self._get(url).json()

    def list_mosaics_in_mosaic_series(self, series_id):
        url = self.base_url + 'basemaps/v1/series/{}/mosaics'.format(series_id)
        resp = self._get(url)
        series = resp.json()
        return series

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

    def get_quads_in_mosaic_for_region(self, mosaic_id, aoi):
        url = self.base_url + f'basemaps/v1/mosaics/{mosaic_id}/quads/search?minimal=true'
        resp = self._post(url, aoi).json()
        return resp['items']

    def get_time_series(self, aoi, start_date, end_date):
        mosaic_series = self.list_mosaic_series(name__is='Global Monthly')['series'][0]
        series_id = mosaic_series['id']
        geometry = aoi[0]['config']
        time_series = []
        mosaics = self.list_mosaics_in_mosaic_series(series_id)['mosaics']
        for mosaic in mosaics:
            date = mosaic['first_acquired']
            if start_date <= date < end_date:
                mosaic_id = mosaic['id']
                quads = [quad for quad in self.get_quads_in_mosaic_for_region(mosaic_id, geometry)]
                mosaic['quads'] = quads
                time_series.append(mosaic)
        return time_series
