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
from urllib.parse import urljoin


from .http import PlanetSession
from . import auth
from . import models

BASE_URL = 'https://api.planet.com/'
ORDERS_API_URL = urljoin(BASE_URL, 'compute/ops/orders/v2/')

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

    def __init__(self, api_key=None, base_url=ORDERS_API_URL):
        '''
        :param str api_key: (opt) API key to use.
            Defaults to environment variable or stored authentication data.
        :param str base_url: (opt) The base URL to use. Defaults to production
            orders API base url.
        '''
        api_key = api_key or auth.find_api_key()
        self.auth = api_key and auth.APIKey(api_key)

        self.base_url = base_url
        if not self.base_url.endswith('/'):
            self.base_url += '/'

    def _check_order_id(self, oid):
        if not oid or not isinstance(oid, str):
            msg = 'Order id ({}) is invalid.'.format(oid)
            raise OrdersClientException(msg)

    def _order_url(self, order_id):
        self._check_order_id
        return self.base_url + order_id

    def _request(self, url, method, body_type, data=None):
        '''Prepare an order API request.

        :param url str: location to make request
        :returns: :py:Class:`planet.api.models.Request`
        '''
        return models.Request(url, self.auth, body_type=body_type,
                              method=method, data=data)

    # def _get(self, url, body_type):
    #     '''Submit a get request and handle response.
    #
    #     :param url str: location to make request
    #     :returns: :py:Class:`planet.api.models.Response`
    #     :raises planet.api.exceptions.APIException: On API error.
    #     '''
    #     with PlanetSession as sess:
    #         request = self._request(url, 'GET')
    #         response = sess.request(request)
    #
    #     return response

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

        url = self.base_url

        LOGGER.debug(order_request.data)
        request = self._request(url, 'POST', models.Order, order_request.data)

        with PlanetSession() as sess:
            order = sess.request(request).body

        return order.id

    def get_order(self, order_id):
        '''Get order details by Order ID.

        :param order_id str: The ID of the order
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        request = self._request(url, 'GET', models.Order)

        with PlanetSession() as sess:
            order = sess.request(request).body

        return order

    def cancel_order(self, order_id):
        '''Cancel a queued order.

        :param order_id str: The ID of the order
        :returns :py:Class:`planet.api.models.Order`: Cancelled order details.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        LOGGER.debug('order id: {}'.format(order_id))
        url = self._order_url(order_id)
        LOGGER.debug('cancelling at {}'.format(url))
        request = self._request(url, 'PUT', models.Order)

        with PlanetSession() as sess:
            order = sess.request(request).body

        return order

    def cancel_orders(self, order_ids):
        '''Cancel queued orders in bulk.
        '''
        raise NotImplementedError

    def aggretated_order_stats(self):
        '''Get aggregated counts of active orders.
        '''
        raise NotImplementedError

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
