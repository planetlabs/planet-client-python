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
from . import filters


class _Base(object):
    '''High-level access to Planet's API.'''
    def __init__(self, api_key=None, base_url='https://api.planet.com/',
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
        self.dispatcher._asyncpool.executor.shutdown(wait=False)

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
        result = self.dispatcher.session.post(self._url('v0/auth/login'), {
            'email': identity,
            'password': credentials
        })
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


def _patch_stats_request(request):
    '''If the request has no filter config, add one that should do what is
    expected (include all items)
    see: PE-11813
    '''
    filt = request.get('filter', {})
    if not filt.get('config', None):
        request['filter'] = filters.date_range('acquired',
                                               gt='1970-01-01T00:00:00Z')
    return request


class ClientV1(_Base):
    '''ClientV1 provides basic low-level access to Planet's API. Only one
    ClientV1 should be in existence for an application. The Client is thread
    safe and takes care to avoid API throttling and also retry any throttled
    requests. Most functions take JSON-like dict representations of API
    request bodies. Return values are usually a subclass of
    :py:class:`planet.api.models.Body`. Any exceptional http responses are
    handled by translation to one of the :py:mod:`planet.api.exceptions`
    classes.
    '''

    def _params(self, kw):
        params = {}
        if 'page_size' in kw:
            params['_page_size'] = kw['page_size']
        if 'sort' in kw and kw['sort']:
            params['_sort'] = ''.join(kw['sort'])
        return params

    def create_search(self, request):
        '''Create a new saved search from the specified request.
        The request must contain a ``name`` property.

        :param request: see :ref:`api-search-request`
        :returns: :py:class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        body = json.dumps(request)
        return self.dispatcher.response(models.Request(
            self._url('data/v1/searches/'), self.auth,
            body_type=models.JSON, data=body, method='POST')).get_body()

    def quick_search(self, request, **kw):
        '''Execute a quick search with the specified request.

        :param request: see :ref:`api-search-request`
        :param \**kw: See Options below
        :returns: :py:class:`planet.api.models.Items`
        :raises planet.api.exceptions.APIException: On API error.

        :Options:

        * page_size (int): Size of response pages
        * sort (string): Sorting order in the form `field (asc|desc)`

        '''
        body = json.dumps(request)
        params = self._params(kw)
        return self.dispatcher.response(models.Request(
            self._url('data/v1/quick-search'), self.auth, params=params,
            body_type=models.Items, data=body, method='POST')).get_body()

    def saved_search(self, sid, **kw):
        '''Execute a saved search by search id.

        :param sid string: The id of the search
        :returns: :py:class:`planet.api.models.Items`
        :raises planet.api.exceptions.APIException: On API error.

        :Options:

        * page_size (int): Size of response pages
        * sort (string): Sorting order in the form `field (asc|desc)`

        '''
        path = 'data/v1/searches/%s/results' % sid
        params = self._params(kw)
        return self._get(self._url(path), body_type=models.Items,
                         params=params).get_body()

    def get_searches(self, quick=False, saved=True):
        '''Get searches listing.

        :param quick bool: Include quick searches (default False)
        :param quick saved: Include saved searches (default True)
        :returns: :py:class:`planet.api.models.Searches`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        params = {}
        if saved and not quick:
            params['search_type'] = 'saved'
        elif quick:
            params['search_type'] = 'quick'
        return self._get(self._url('data/v1/searches/'),
                         body_type=models.Searches, params=params).get_body()

    def stats(self, request):
        '''Get stats for the provided request.

        :param request dict: A search request that also contains the 'interval'
                             property.
        :returns: :py:class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        # work-around for API bug
        request = _patch_stats_request(request)
        body = json.dumps(request)
        return self.dispatcher.response(models.Request(
            self._url('data/v1/stats'), self.auth,
            body_type=models.JSON, data=body, method='POST')).get_body()

    def get_assets(self, item):
        '''Get the assets for the provided item representations.

        Item representations are obtained from search requests.

        :param request dict: An item representation from the API.
        :returns: :py:class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        assets_url = item['_links']['assets']
        return self._get(assets_url).get_body()

    def activate(self, asset):
        '''Request activation of the specified asset representation.

        Asset representations are obtained from :py:meth:`get_assets`.

        :param request dict: An asset representation from the API.
        :returns: :py:class:`planet.api.models.Body` with no response content
        :raises planet.api.exceptions.APIException: On API error.
        '''
        activate_url = asset['_links']['activate']
        return self._get(activate_url, body_type=models.Body).get_body()

    def download(self, asset, callback=None):
        '''Download the specified asset. If provided, the callback will be
        invoked asynchronously. Otherwise it is up to the caller to handle the
        response Body.

        :param asset dict: An asset representation from the API
        :param callback: An optional function to aysnchronsously handle the
                         download. See :py:func:`planet.api.write_to_file`
        :returns: :py:Class:`planet.api.models.Response` containing a
                  :py:Class:`planet.api.models.Body` of the asset.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        download_url = asset['location']
        return self._get(download_url, models.Body, callback=callback)

    def get_item(self, item_type, id):
        '''Get the an item response for the given item_type and id

        :param item_type str: A valid item-type
        :param id str: The id of the item
        :returns: :py:Class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = 'data/v1/item-types/%s/items/%s' % (item_type, id)
        return self._get(url).get_body()

    def get_assets_by_id(self, item_type, id):
        '''Get an item's asset response for the given item_type and id

        :param item_type str: A valid item-type
        :param id str: The id of the item
        :returns: :py:Class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = 'data/v1/item-types/%s/items/%s/assets' % (item_type, id)
        return self._get(url).get_body()
