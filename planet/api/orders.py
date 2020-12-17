# Copyright 2020 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Functionality for interacting with the orders api"""

import copy
import json
import itertools
import logging
import os
import time

from .http import PlanetSession
from . import auth
from . import models
from .. import specs

PLANET_BASE_URL = 'https://api.planet.com/'
BASE_URL = PLANET_BASE_URL + 'compute/ops/'
STATS_PATH = 'stats/orders/v2/'
ORDERS_PATH = 'orders/v2/'
BULK_PATH = 'bulk/orders/v2/'

ORDERS_STATES_COMPLETE = ['success', 'partial', 'cancelled']
ORDERS_STATES = ['queued', 'running', 'failed'] + ORDERS_STATES_COMPLETE

LOGGER = logging.getLogger(__name__)


class OrdersClientException(Exception):
    """Exceptions thrown by OrdersClient"""
    pass


class OrdersClient():
    """High-level access to Planet's orders API.

    Basic Usage::

      from planet.api.orders_client import OrdersClient
      cl = OrdersClient('api_key')
      order = cl.get_order('order_id')

    :param api_key: API key to use. Defaults to environment variable or
        stored authentication data.
    :type api_key: str, optional
    :param base_url: The base URL to use. Defaults to production orders API
        base url.
    :type base_url: int, optional
    """
    def __init__(self, api_key=None, base_url=BASE_URL):
        api_key = api_key or auth.find_api_key()
        self.auth = api_key and auth.APIKey(api_key)

        self._base_url = base_url
        if not self._base_url.endswith('/'):
            self._base_url += '/'

    @staticmethod
    def _check_order_id(oid):
        if not oid or not isinstance(oid, str):
            msg = 'Order id ({}) is invalid.'.format(oid)
            raise OrdersClientException(msg)

    def _orders_url(self):
        return self._base_url + ORDERS_PATH

    def _stats_url(self):
        return self._base_url + STATS_PATH

    def _order_url(self, order_id):
        self._check_order_id
        return self._orders_url() + order_id

    def _bulk_url(self):
        return self._base_url + BULK_PATH

    def _request(self, url, method, body_type, data=None, params=None):
        return models.Request(url, self.auth, body_type=body_type,
                              method=method, data=data, params=params)

    def _get(self, url, body_type, params=None):
        request = self._request(url, 'GET', body_type)
        return self._do_request(request)

    def _put(self, url, body_type):
        request = self._request(url, 'PUT', body_type)
        return self._do_request(request)

    def _post(self, url, body_type, data):
        LOGGER.debug('post data: {}'.format(data))
        request = self._request(url, 'POST', body_type, data)
        return self._do_request(request)

    def _do_request(self, request):
        with PlanetSession() as sess:
            body = sess.request(request).body
        return body

    def _get_pages(self, url, get_next_fcn, params=None):
        request = self._request(url, 'GET', models.JSON, params=params)

        with PlanetSession() as sess:
            LOGGER.debug('getting first page')
            body = sess.request(request).body
            yield body

            next_url = get_next_fcn(body)
            while(next_url):
                LOGGER.debug('getting next page')
                request.url = next_url
                body = sess.request(request).body
                yield body
                next_url = get_next_fcn(body)

    def create_order(self, order_request):
        '''Create an order request.

        :param order_request: order request details
        :type order_request: dict
        :return: The ID of the order
        :rtype: str
        '''
        if not isinstance(order_request, OrderDetails):
            order_request = OrderDetails(order_request)

        url = self._orders_url()

        body = self._post(url, models.JSON, order_request.data)
        order = Order(body.data)
        return order.id

    def get_order(self, order_id):
        '''Get order details by Order ID.

        :param order_id: The ID of the order
        :type order_id: str
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        body = self._get(url, models.JSON)
        return Order(body.data)

    def cancel_order(self, order_id):
        '''Cancel a queued order.

        According to the API docs, cancel order should return the cancelled
        order details. But testing reveals that an empty response is returned
        upon success.

        :param order_id: The ID of the order
        :type order_id: str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        body = self._put(url, models.Body)
        LOGGER.debug('cancel order response body: {}'.format(body.get_raw()))
        assert body.get_raw() == ''

    def cancel_orders(self, order_ids):
        '''Cancel queued orders in bulk.

        order_ids is required here even if it is an empty string. This is to
        avoid accidentally canceeling all orders when only a subset was
        desired.

        :param list of str order_ids: The IDs of the orders. If empty, all
            orders in a pre-running state will be cancelled.
        :returns dict: Results of the bulk cancel request.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._bulk_url() + 'cancel'
        cancel_body = {}
        if order_ids:
            cancel_body['order_ids'] = order_ids

        # was sending the body as params without json.dumps()
        body = self._post(url, models.JSON, json.dumps(cancel_body))
        return body.data

    def aggregated_order_stats(self):
        '''Get aggregated counts of active orders.

        :returns dict: aggregated order counts
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._stats_url()
        res = self._get(url, models.JSON)
        return res.data

    def download_asset(self, location, filename=None, directory=None,
                       callback=None, overwrite=True):
        '''Download ordered asset.

        If provided, the callback will be invoked 4 different ways:

        * First as ``callback(start=body)``
        * For each chunk of data written as
          ``callback(wrote=chunk_size_in_bytes, total=all_byte_cnt)``
        * Upon completion as ``callback(finish=body)``
        * Upon skip as ``callback(skip=body)``

        simple reporter callback example::

            def callback(start=None, wrote=None, total=None,
                         finish=None, skip=None):
                if start: print(start)
                if wrote: print(wrote)
                if total: print(total)
                if finish: print(finish)
                if skip: print(skip)

        :param location: Download location url including download token
        :type location: str
        :param filename: Name to assign to downloaded file. Defaults to the
            name given in the response from the download location.
        :type filename: str, optional
        :param directory: Directory to write to. Defaults to current
            directory.
        :type directory: str, optional
        :param callback: A function handle of the form
            ``callback(start, wrote, total, finish, skip)`` that receives write
            progress. Defaults to None
        :type callback: function, optional
        :param overwrite: Overwrite any existing files. Defaults to True
        :type overwrite: bool
        :return: Path to downloaded file.
        :rtype: str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        body = self._get(location, models.Body)
        dl_path = os.path.join(directory or '.', filename or body.name)
        body.write_to_file(dl_path, overwrite=overwrite, callback=callback)
        return dl_path

    def download_order(self, order_id, directory=None, callback=None,
                       overwrite=True):
        '''Download all assets in an order.

        Uses `download_asset` to downloads each asset in an order.
        The arguments
        `directory`, `callback`, and `overwrite` are used as described in
        :py:meth:`download_asset`

        :param order_id: The ID of the order
        :type order_id: str
        :param directory: Directory to write to. Defaults to current
            directory.
        :type directory: str, optional
        :param callback: A function handle of the form
            ``callback(start, wrote, total, finish, skip)`` that receives write
            progress. Invoked as described in Defaults to None
        :type callback: function, optional
        :param overwrite: Overwrite any existing files. Defaults to True
        :type overwrite: bool, optional
        :return: Paths to downloaded files.
        :rtype: list of str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        order = self.get_order(order_id)
        locations = order.locations
        LOGGER.info('downloading {} assets from order {}'.format(
            len(locations), order_id))

        filenames = [self.download_asset(location,
                                         directory=directory,
                                         callback=callback,
                                         overwrite=overwrite)
                     for location in locations]
        return filenames

    def wait_for_complete(self, order_id, wait=10, callback=None):
        '''Poll for order status until order is complete.

        If provided, the callback will be invoked as:

        * ``callback(state=state)``

        simple reporter callback example::

            def callback(state):
                print(state)

        :param order_id: The ID of the order
        :type order_id: str
        :param int wait: Time (in seconds) between polls
        :type wait: int
        :param callback: A function handle of the form
            ``callback(state)`` that receives poll progress. Defaults to None
        :type callback: function, optional
        :return: Completed state of the order
        :rtype: str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        completed = False
        while not completed:
            t = time.time()
            order = self.get_order(order_id)
            state = order.state
            callback(state=state)
            LOGGER.info('order state: {}'.format(state))

            completed = state in ORDERS_STATES_COMPLETE

            if not completed:
                sleep_time = max(wait-(time.time()-t), 0)
                LOGGER.info('sleeping {}s'.format(sleep_time))
                time.sleep(sleep_time)
        return state

    def list_orders(self, state=None, limit=None):
        '''Get all order requests.

        :param state: Filter orders to given state. Defaults to None
        :type state: str, optional
        :param state: Limit orders to given limit. Defaults to None
        :type state: int, optional
        :return: User :py:Class:`planet.api.models.Order` objects that match
            the query
        :rtype: iterator
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._orders_url()
        if state:
            self._check_state(state)
            params = {"state": state}
        else:
            params = None

        orders = self._get_orders(url, params)

        if limit:
            orders = itertools.islice(orders, limit)
        return orders

    @staticmethod
    def _check_state(state):
        if state not in ORDERS_STATES:
            msg = 'Order state (\'{}\') should be one of: {}'.format(
                    state, ORDERS_STATES)
            raise OrdersClientException(msg)

    def _get_orders(self, url, params=None):
        get_next_fcn = Orders.next_link
        bodies = self._get_pages(url, get_next_fcn, params=params)
        orders = Orders.items_iter(bodies)
        return orders


class Orders():
    # TODO: the delegation between Orders and OrdersClient could
    # likely be improved here
    @staticmethod
    def next_link(body):
        try:
            next_link = body.data['_links']['next']
            LOGGER.debug('next link: {}'.format(next_link))
        except KeyError:
            next_link = False
        return next_link

    @staticmethod
    def items_iter(bodies):
        def _get_orders(body):
            orders = body.data['orders']
            return (Order(o) for o in orders)

        all_orders = itertools.chain.from_iterable(
            (_get_orders(body) for body in bodies))
        return all_orders


class Order():
    '''Managing description of an order returned from Orders API.

    :param data: Response json describing order
    :type data: dict
    '''
    LINKS_KEY = '_links'
    RESULTS_KEY = 'results'
    LOCATION_KEY = 'location'

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return "<Order> " + json.dumps(self.data)

    @property
    def results(self):
        '''Results for each item in order.

        :return: result for each item in order
        :rtype: list of dict
        '''
        links = self.data[self.LINKS_KEY]
        results = links.get(self.RESULTS_KEY, None)
        return results

    @property
    def locations(self):
        '''Download locations for order results.

        :return: download locations in order
        :rtype: list of str
        '''
        return list(r[self.LOCATION_KEY] for r in self.results)

    @property
    def state(self):
        '''State of the order.

        :return: state of order
        :rtype: str
        '''
        return self.data['state']

    @property
    def id(self):
        '''ID of the order.

        :return: id of order
        :rtype: str
        '''
        return self.data['id']


class OrderDetailsException(Exception):
    """Exceptions thrown by OrderDetails"""
    pass


class OrderDetails():
    '''Validating and preparing an order description for submission.

    :param details: Specification of order to be created.
    :type details: dict
    :raises OrderDetailsException: When provided `item_type` or
        `product_bundle` is not supported.
    '''
    BUNDLE_KEY = 'product_bundle'

    def __init__(self, details):
        self._data = copy.deepcopy(details)
        self._validate_details()

    @property
    def data(self):
        '''The order details as a string representing json.

        :return: order details json
        :rtype: str
        '''
        return json.dumps(self._data)

    def _validate_details(self):
        '''Try valiently to get details to match schema.

        Checks that details match the schema and, where possible, change
        the details to fit the schema (e.g. change capitalization')
        '''
        products = self._data['products']
        for p in products:
            self._validate_bundle(p)
            self._validate_item_type(p)

    def _validate_bundle(self, product):
        supported = specs.get_product_bundles()
        self._substitute_supported(product, self.BUNDLE_KEY, supported)

    def _validate_item_type(self, product):
        key = 'item_type'
        bundle = product[self.BUNDLE_KEY]
        supported = specs.get_item_types(bundle)
        self._substitute_supported(product, key, supported)

    @staticmethod
    def _substitute_supported(product, key, supported):
        try:
            matched_type = specs.get_match(product[key], supported)
            LOGGER.debug('{}: {}'.format(key, matched_type))
            product[key] = matched_type
        except(StopIteration):
            msg = '{} - \'{}\' not in {}'.format(
                key, product[key], supported)
            raise OrderDetailsException(msg)
