# Copyright 2020 Planet Labs, Inc.
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
import logging

import pytest

from planet.api import orders

LOGGER = logging.getLogger(__name__)


def test_OrderDetails_substitute_supported():
    key = 'abc'
    supported = ['Supported', 'whyamihere']

    # ensure capitalization doesn't matter
    valid_product = {key: 'supported'}
    orders.OrderDetails._substitute_supported(valid_product, key, supported)
    assert valid_product[key] == 'Supported'

    # ensure an exception is raised when the entry is not supported
    invalid_product = {key: 'notsupported'}
    with pytest.raises(orders.OrderDetailsException):
        orders.OrderDetails._substitute_supported(
            invalid_product, key, supported)


def test_OrderDetails__validate_details_valid(order_details):
    order_details['products'][0]['product_bundle'] = 'ANALYTIC'
    order_details['products'][0]['item_type'] = 'psorthotile'

    _ = orders.OrderDetails(order_details)


def test_OrderDetails__validate_details_invalid(order_details):
    invalid_bundle = order_details.copy()
    invalid_bundle['products'][0]['product_bundle'] = 'nope'

    with pytest.raises(orders.OrderDetailsException):
        _ = orders.OrderDetails(invalid_bundle)

    invalid_item = order_details.copy()
    invalid_item['products'][0]['product_bundle'] = 'ANALYTIC'
    invalid_item['products'][0]['item_type'] = 'nope'

    with pytest.raises(orders.OrderDetailsException):
        _ = orders.OrderDetails(invalid_item)
