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


LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://api.planet.com/'

ORDERS_API_URL = urljoin(BASE_URL, 'compute/ops/orders/v2/')


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

    def _order_url(self, order_id):
        return urljoin(self.base_url, order_id)

    def _request(self, url, method, body_type):
        '''Prepare an order API request.

        :param url str: location to make request
        :returns: :py:Class:`planet.api.models.Request`
        '''
        return models.Request(url, self.auth, body_type=body_type,
                              method=method)

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
        '''
        raise NotImplementedError

    def create_order(self, order_request):
        '''Create an order request.

        :returns str: The ID of the order
        '''
        raise NotImplementedError

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
        '''
        raise NotImplementedError

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
