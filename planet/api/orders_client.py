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
# import logging

"""Functionality for interacting with the orders api"""

import logging

from .http import PlanetSession
from . import auth
from . import models

PLANET_BASE_URL = 'https://api.planet.com/'
BASE_URL = PLANET_BASE_URL + 'compute/ops/'
STATS_PATH = 'stats/orders/v2/'
ORDERS_PATH = 'orders/v2/'


LOGGER = logging.getLogger(__name__)


class OrdersClientException(Exception):
    """Exceptions thrown by Orders Client"""
    pass


class OrdersClient(object):
    """High-level access to Planet's orders API.

    Basic Usage::
      >>>
      >> from planet.api.orders_client import OrdersClient
      >> cl = OrdersClient('api_key')
      >> order = cl.get_order('order_id')
      <models.Order>
    """
    def __init__(self, api_key=None, base_url=BASE_URL):
        '''
        :param str api_key: (opt) API key to use.
            Defaults to environment variable or stored authentication data.
        :param str base_url: (opt) The base URL to use. Defaults to production
            orders API base url.
        '''
        api_key = api_key or auth.find_api_key()
        self.auth = api_key and auth.APIKey(api_key)

        self._base_url = base_url
        if not self._base_url.endswith('/'):
            self._base_url += '/'

    def _check_order_id(self, oid):
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

    def _request(self, url, method, body_type, data=None):
        '''Prepare an order API request.

        :param url str: location to make request
        :returns: :py:Class:`planet.api.models.Request`
        '''
        return models.Request(url, self.auth, body_type=body_type,
                              method=method, data=data)

    def _get(self, url, body_type):
        request = self._request(url, 'GET', body_type)
        return self._do_request(request)

    def _put(self, url, body_type):
        request = self._request(url, 'PUT', body_type)
        return self._do_request(request)

    def _post(self, url, body_type, data):
        request = self._request(url, 'POST', body_type, data)
        return self._do_request(request)

    def _do_request(self, request):
        with PlanetSession() as sess:
            body = sess.request(request).body
        return body

    def list_orders(self):
        '''Get all order requests.

        :returns: :py:Class:`planet.api.models.Orders`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        # url = self.base_url
        #
        # request = self._request(url, 'GET', models.Orders)
        #
        # with PlanetSession() as sess:
        #     orders = sess.request(request).body
        #
        # return orders
        raise NotImplementedError

    def create_order(self, order_request):
        '''Create an order request.

        :param dict order_request: order request details
        :returns str: The ID of the order
        '''
        if not isinstance(order_request, models.OrderDetails):
            order_request = models.OrderDetails(order_request)

        url = self._orders_url()

        order = self._post(url, models.Order, order_request.data)
        return order.id

    def get_order(self, order_id):
        '''Get order details by Order ID.

        :param order_id str: The ID of the order
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        order = self._get(url, models.Order)
        return order

    def cancel_order(self, order_id):
        '''Cancel a queued order.

        :param order_id str: The ID of the order
        :returns :py:Class:`planet.api.models.Order`: Cancelled order details.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        order = self._put(url, models.Order)
        return order

    def cancel_orders(self, order_ids):
        '''Cancel queued orders in bulk.
        '''
        raise NotImplementedError

    def aggregated_order_stats(self):
        '''Get aggregated counts of active orders.

        :returns dict: aggregated order counts
        :raises planet.api.exceptions.APIException: On API error.

        '''
        url = self._stats_url()
        res = self._get(url, models.JSON)
        return res.data

    def download_order(self, order_id, wait=False):
        '''Download ordered asset

        :param order_id str: The ID of the order
        '''
        raise NotImplementedError


# class BaseClient(object):
#     def _url(self, path):
#         if path.startswith('http'):
#             url = path
#         else:
#             url = self.base_url + path
#         return url
#
#     def _request(self, path, body_type=models.JSON, params=None, auth=None):
#         return models.Request(self._url(path), auth or self.auth, params,
#                               body_type)
#
#     def _get(self, path, body_type=models.JSON, params=None, callback=None):
#         # convert any JSON objects to text explicitly
#         for k, v in (params or {}).items():
#             if isinstance(v, dict):
#                 params[k] = json.dumps(v)
#
#         request = self._request(path, body_type, params)
#         response = self.dispatcher.response(request)
#         if callback:
#             response.get_body_async(callback)
#         return response
