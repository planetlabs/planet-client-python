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
import asyncio
import copy
import json
# import itertools
import logging
import os
import time

# from aiostream import stream

from . import models
from .. import constants, specs


BASE_URL = constants.PLANET_BASE_URL + 'compute/ops/'
STATS_PATH = 'stats/orders/v2/'
ORDERS_PATH = 'orders/v2/'
BULK_PATH = 'bulk/orders/v2/'

ORDERS_STATES_COMPLETE = ['success', 'partial', 'cancelled', 'failed']
ORDERS_STATES_IN_PROGRESS = ['queued', 'running']
ORDERS_STATES = ORDERS_STATES_IN_PROGRESS + ORDERS_STATES_COMPLETE

LOGGER = logging.getLogger(__name__)


class OrdersClientException(Exception):
    """Exceptions thrown by OrdersClient"""
    pass


class AOrdersClient():
    """High-level asynchronous access to Planet's orders API.

    Basic Usage::

      from planet.api.orders_client import AOrdersClient
      cl = AOrdersClient('api_key')
      order = cl.get_order('order_id')

    :param api_key: API key to use. Defaults to environment variable or
        stored authentication data.
    :type api_key: str, optional
    :param base_url: The base URL to use. Defaults to production orders API
        base url.
    :type base_url: int, optional
    """
    def __init__(self, session, base_url=BASE_URL):
        self._session = session

        self._base_url = base_url
        if not self._base_url.endswith('/'):
            self._base_url += '/'

    @staticmethod
    def _check_order_id(oid):
        if not oid or not isinstance(oid, str):
            raise OrdersClientException(f'Order id ({oid}) is invalid.')

    def _orders_url(self):
        return self._base_url + ORDERS_PATH

    def _stats_url(self):
        return self._base_url + STATS_PATH

    def _order_url(self, order_id):
        self._check_order_id
        return self._orders_url() + order_id

    def _bulk_url(self):
        return self._base_url + BULK_PATH

    def _request(self, url, method, data=None, params=None, json=None):
        return models.Request(url, method=method, data=data, params=params,
                              json=json)

    async def _do_request(self, request):
        return await self._session.request(request)

    async def create_order(self, order_details):
        '''Create an order request.

        :param order_request: order request details
        :type order_request: dict or OrderDetails
        :return: The ID of the order
        :rtype: str
        '''
        if not isinstance(order_details, OrderDetails):
            order_details = OrderDetails(order_details)

        url = self._orders_url()
        req = self._request(url, method='POST', data=order_details.data)
        resp = await self._do_request(req)

        order = Order(resp.json())
        return order.id

    async def get_order(self, order_id):
        '''Get order details by Order ID.

        :param order_id: The ID of the order
        :type order_id: str
        :returns: :py:Class:`planet.api.models.Order`
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        req = self._request(url, method='GET')
        resp = await self._do_request(req)

        order = Order(resp.json())
        return order

    async def cancel_order(self, order_id):
        '''Cancel a queued order.

        According to the API docs, cancel order should return the cancelled
        order details. But testing reveals that an empty response is returned
        upon success.

        :param order_id: The ID of the order
        :type order_id: str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._order_url(order_id)
        req = self._request(url, method='PUT')
        await self._do_request(req)

    async def cancel_orders(self, order_ids=None):
        '''Cancel queued orders in bulk.

        :param list of str order_ids: The IDs of the orders. If empty, all
            orders in a pre-running state will be cancelled.
        :returns dict: Results of the bulk cancel request.
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._bulk_url() + 'cancel'
        cancel_body = {}
        if order_ids:
            cancel_body['order_ids'] = order_ids

        req = self._request(url, method='POST', json=cancel_body)
        resp = await self._do_request(req)
        return resp.json()

    def aggregated_order_stats(self):
        '''Get aggregated counts of active orders.

        :returns dict: aggregated order counts
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._stats_url()
        res = self._get(url, models.JSON)
        return res.data

    async def download_asset(self, location, filename=None, directory=None,
                             overwrite=True, progress_bar=False):
        '''Download ordered asset.

        :param location: Download location url including download token
        :type location: str
        :param filename: Name to assign to downloaded file. Defaults to the
            name given in the response from the download location.
        :type filename: str, optional
        :param directory: Directory to write to. Defaults to current
            directory.
        :type directory: str, optional
        :param overwrite: Overwrite any existing files. Defaults to True
        :type overwrite: bool
        :return: Path to downloaded file.
        :rtype: str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        req = self._request(location, method='GET')

        async with self._session.stream(req) as resp:
            body = models.StreamingBody(resp)
            dl_path = os.path.join(directory or '.', filename or body.name)
            await body.write(dl_path,
                             overwrite=overwrite,
                             progress_bar=progress_bar)
        return dl_path

    async def download_order(self, order_id, directory=None, overwrite=True,
                             progress_bar=False):
        '''Download all assets in an order.

        :param order_id: The ID of the order
        :type order_id: str
        :param directory: Directory to write to. Defaults to current
            directory.
        :type directory: str, optional
        :param overwrite: Overwrite any existing files. Defaults to True
        :type overwrite: bool, optional
        :return: Paths to downloaded files.
        :rtype: list of str
        :raises planet.api.exceptions.APIException: On API error.
        '''
        order = await self.get_order(order_id)
        locations = order.locations
        LOGGER.info(
            f'downloading {len(locations)} assets from order {order_id}'
        )
        filenames = [await self.download_asset(location,
                                               directory=directory,
                                               overwrite=overwrite,
                                               progress_bar=progress_bar)
                     for location in locations]
        return filenames

    async def poll(self, order_id, state=None, wait=10):
        '''Poll for order status until order reaches desired state.

        :param order_id: The ID of the order
        :type order_id: str
        :param state: State to poll until. If multiple, use list. Defaults to
            any completed state.
        :type state: str, list of str
        :param int wait: Time (in seconds) between polls
        :type wait: int
        :return: Completed state of the order
        :rtype: str
        :raises planet.api.exceptions.APIException: On API error.
        :raises OrdersClientException: If state is not supported.

        '''
        completed = False

        if state:
            if state not in ORDERS_STATES:
                raise OrdersClientException(
                    f'{state} should be one of'
                    f'{ORDERS_STATES}')
            states = [state]
        else:
            states = ORDERS_STATES_COMPLETE

        while not completed:
            t = time.time()
            order = await self.get_order(order_id)
            state = order.state
            LOGGER.info(f'order {order_id} state: {state}')

            completed = state in states
            if not completed:
                sleep_time = max(wait-(time.time()-t), 0)
                LOGGER.info(f'sleeping {sleep_time}s')
                await asyncio.sleep(sleep_time)
        return state

    async def list_orders(self, state=None, limit=None):
        '''Get all order requests.

        :param state: Filter orders to given state. Defaults to None
        :type state: str, optional
        :param state: Limit orders to given limit. Defaults to None
        :type state: int, optional
        :return: User :py:Class:`planet.api.models.Order` objects that match
            the query
        :rtype: generator
        :raises planet.api.exceptions.APIException: On API error.
        '''
        url = self._orders_url()
        if state:
            self._check_state(state)
            params = {"state": state}
        else:
            params = None

        return await self._get_orders(url, params=params, limit=limit)

    async def _get_orders(self, url, params=None, limit=None):
        request = self._request(url, 'GET', params=params)

        orders_paged = OrdersPaged(request, self._do_request, limit=limit)
        return [o async for o in orders_paged]

    @staticmethod
    def _check_state(state):
        if state not in ORDERS_STATES:
            raise OrdersClientException(
                f'Order state (\'{state}\') should be one of: '
                f'{ORDERS_STATES}'
            )


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


class OrdersPaged(models.Paged):
    LINKS_KEY = '_links'
    NEXT_KEY = 'next'
    ITEMS_KEY = 'orders'

    async def __anext__(self):
        return Order(await super().__anext__())


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
            LOGGER.debug(f'{key}: {matched_type}')
            product[key] = matched_type
        except(StopIteration):
            raise OrderDetailsException(
                f'{key} - \'{product[key]}\' not in {supported}'
            )
