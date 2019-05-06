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
        if not self.base_url.endswith('/'):
            self.base_url += '/'
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
        result = self.dispatcher.session.post(self._url('v0/auth/login'),
                                              json={
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
        if 'strict' in kw:
            # This transforms a Python boolean into a JSON boolean
            params['strict'] = json.dumps(kw['strict'])
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
        :param **kw: See Options below
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

    def get_mosaic_series(self, series_id):
        '''Get information pertaining to a mosaics series
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        url = self._url('basemaps/v1/series/{}'.format(series_id))
        return self._get(url, models.JSON).get_body()

    def get_mosaics_for_series(self, series_id):
        '''Get list of mosaics available for a series
        :returns: :py:Class:`planet.api.models.Mosaics`
        '''
        url = self._url('basemaps/v1/series/{}/mosaics'.format(series_id))
        return self._get(url, models.Mosaics).get_body()

    def get_mosaics(self, name_contains=None):
        '''Get information for all mosaics accessible by the current user.

        :returns: :py:Class:`planet.api.models.Mosaics`
        '''
        params = {}
        if name_contains:
            params['name__contains'] = name_contains
        url = self._url('basemaps/v1/mosaics')
        return self._get(url, models.Mosaics, params=params).get_body()

    def get_mosaic_by_name(self, name):
        '''Get the API representation of a mosaic by name.

        :param name str: The name of the mosaic
        :returns: :py:Class:`planet.api.models.Mosaics`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        params = {'name__is': name}
        url = self._url('basemaps/v1/mosaics')
        return self._get(url, models.Mosaics, params=params).get_body()

    def get_quads(self, mosaic, bbox=None):
        '''Search for quads from a mosaic that are inside the specified
        bounding box.  Will yield all quads if no bounding box is specified.

        :param mosaic dict: A mosaic representation from the API
        :param bbox tuple: A lon_min, lat_min, lon_max, lat_max area to search
        :returns: :py:Class:`planet.api.models.MosaicQuads`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        if bbox is None:
            # Some bboxes can slightly exceed backend min/max latitude bounds
            xmin, ymin, xmax, ymax = mosaic['bbox']
            bbox = (max(-180, xmin), max(-85, ymin),
                    min(180, xmax), min(85, ymax))
        url = mosaic['_links']['quads']
        url = url.format(lx=bbox[0], ly=bbox[1], ux=bbox[2], uy=bbox[3])
        return self._get(url, models.MosaicQuads).get_body()

    def get_quad_by_id(self, mosaic, quad_id):
        '''Get a quad response for a specific mosaic and quad.

        :param mosaic dict: A mosaic representation from the API
        :param quad_id str: A quad id (typically <xcoord>-<ycoord>)
        :returns: :py:Class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        path = 'basemaps/v1/mosaics/{}/quads/{}'.format(mosaic['id'], quad_id)
        return self._get(self._url(path)).get_body()

    def get_quad_contributions(self, quad):
        '''Get information about which scenes contributed to a quad.

        :param quad dict: A quad representation from the API
        :returns: :py:Class:`planet.api.models.JSON`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = quad['_links']['items']
        return self._get(url).get_body()

    def download_quad(self, quad, callback=None):
        '''Download the specified mosaic quad. If provided, the callback will
        be invoked asynchronously.  Otherwise it is up to the caller to handle
        the response Body.

        :param asset dict: A mosaic quad representation from the API
        :param callback: An optional function to aysnchronsously handle the
                         download. See :py:func:`planet.api.write_to_file`
        :returns: :py:Class:`planet.api.models.Response` containing a
                  :py:Class:`planet.api.models.Body` of the asset.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        download_url = quad['_links']['download']
        return self._get(download_url, models.Body, callback=callback)

    def check_analytics_connection(self):
        '''
        Validate that we can use the Analytics API. Useful to test connectivity
        to test environments.
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        return self._get(self._url('analytics/health')).get_body()

    def wfs_conformance(self):
        '''
        Details about WFS3 conformance
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        return self._get(self._url('analytics/conformance')).get_body()

    def list_analytic_subscriptions(self, feed_id):
        '''
        Get subscriptions that the authenticated user has access to
        :param feed_id str: Return subscriptions associated with a particular
        feed only.
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.Subscriptions`
        '''
        params = {'feedID': feed_id}
        url = self._url('analytics/subscriptions')
        return self._get(url, models.Subscriptions, params=params).get_body()

    def get_subscription_info(self, subscription_id):
        '''
        Get the information describing a specific subscription.
        :param subscription_id:
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        url = self._url('analytics/subscriptions/{}'.format(subscription_id))
        return self._get(url, models.JSON).get_body()

    def list_analytic_feeds(self, stats):
        '''
        Get collections that the authenticated user has access to
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.Feeds`
        '''
        params = {'stats': stats}
        url = self._url('analytics/feeds')
        return self._get(url, models.Feeds, params=params).get_body()

    def get_feed_info(self, feed_id):
        '''
        Get the information describing a specific collection.
        :param subscription_id:
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        url = self._url('analytics/feeds/{}'.format(feed_id))
        return self._get(url, models.JSON).get_body()

    def list_analytic_collections(self):
        '''
        Get collections that the authenticated user has access to
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.WFS3Collections`
        '''
        params = {}
        url = self._url('analytics/collections')
        return self._get(url, models.WFS3Collections,
                         params=params).get_body()

    def get_collection_info(self, subscription_id):
        '''
        Get the information describing a specific collection.
        :param subscription_id:
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.JSON`
        '''
        url = 'analytics/collections/{}'.format(subscription_id)
        return self._get(self._url(url), models.JSON).get_body()

    def list_collection_features(self,
                                 subscription_id,
                                 bbox=None,
                                 time_range=None,
                                 before=None,
                                 after=None,
                                 ):
        '''
        List features for an analytic subscription.
        :param subscription_id:
        :param time_range str: ISO format datetime interval.
        :param bbox tuple: A lon_min, lat_min, lon_max, lat_max area to search
        :param before str: return features published before item with given ID
        :param after str: return features published after item with given ID
        :raises planet.api.exceptions.APIException: On API error.
        :returns: :py:Class:`planet.api.models.WFS3Features`
        '''
        params = {}

        if bbox:
            params['bbox'] = ','.join([str(b) for b in bbox])
        if time_range:
            params['time'] = time_range
        if before:
            params['before'] = before
        if after:
            params['after'] = after

        url = self._url('analytics/collections/{}/items'.format(
            subscription_id))
        return self._get(url, models.WFS3Features, params=params).get_body()

    def get_associated_resource_for_analytic_feature(self,
                                                     subscription_id,
                                                     feature_id,
                                                     resource_type):
        '''
        Get resource associated with some feature in an analytic subscription.
        Response might be JSON or a TIF, depending on requested resource.
        :param subscription_id str: ID of subscription
        :param feature_id str: ID of feature
        :param resource_type str: Type of resource to request.
        :raises planet.api.exceptions.APIException: On API error or resource
        type unavailable.
        :returns: :py:Class:`planet.api.models.JSON` for resource type
        `source-image-info`,  but can also return
        :py:Class:`planet.api.models.Response` containing a
        :py:Class:`planet.api.models.Body` of the resource.
        '''
        url = self._url(
            'analytics/collections/{}/items/{}/resources/{}'.format(
                subscription_id, feature_id, resource_type))
        response = self._get(url).get_body()
        return response

    def get_orders(self):
        '''Get information for all pending and completed order requests for
        the current user.

        :returns: :py:Class:`planet.api.models.Orders`
        '''

        # TODO filter 'completed orders', 'in progress orders', 'all orders'?
        url = self._url('compute/ops/orders/v2')
        orders = (self._get(url, models.Orders).get_body())
        return orders

    def get_individual_order(self, order_id):
        '''Get order request details by Order ID.

        :param order_id str: The ID of the Order
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._url('compute/ops/orders/v2/{}'.format(order_id))
        return self._get(url, models.Order).get_body()

    def cancel_order(self, order_id):
        '''Cancel a running order by Order ID.

        :param order_id str: The ID of the Order to cancel
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._url('compute/ops/orders/v2/{}'.format(order_id))
        return self.dispatcher.response(models.Request(url, self.auth,
                                                       body_type=models.Order,
                                                       method='PUT')
                                        ).get_body()

    def create_order(self, request):
        '''Create an order.

        :param asset:
        :returns: :py:Class:`planet.api.models.Response` containing a
                  :py:Class:`planet.api.models.Body` of the asset.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._url('compute/ops/orders/v2')
        body = json.dumps(request)
        return self.dispatcher.response(models.Request(url, self.auth,
                                                       body_type=models.Order,
                                                       data=body,
                                                       method='POST')
                                        ).get_body()

    def download_order(self, order_id, callback=None):
        '''Download all items in an order.

        :param order_id: ID of order to download
        :returns: :py:Class:`planet.api.models.Response` containing a
                  :py:Class:`planet.api.models.Body` of the asset.
        :raises planet.api.exceptions.APIException: On API error.
        '''

        url = self._url('compute/ops/orders/v2/{}'.format(order_id))

        order = self._get(url, models.Order).get_body()
        locations = order.get_locations()
        return self._get(locations, models.JSON, callback=callback)

    def download_location(self, location, callback=None):
        '''Download an item in an order.

        :param location: location URL of item
        :returns: :py:Class:`planet.api.models.Response` containing a
                  :py:Class:`planet.api.models.Body` of the asset.
        :raises planet.api.exceptions.APIException: On API error.
        '''

        return self._get(location, models.JSON, callback=callback)
