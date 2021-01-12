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


@pytest.fixture
def order_description():
    test_order = {
        "_links": {
            "_self": "selflocation",
            "results": [
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.262Z",
                    "location": "location1",
                    "name": "name1"
                },
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.264Z",
                    "location": "location2",
                    "name": "name2"
                },
                {
                    "delivery": "success",
                    "expires_at": "2020-12-04T22:25:30.267Z",
                    "location": "location3",
                    "name": "name3"
                }
            ]
        },
        "created_on": "2020-12-03T22:20:04.153Z",
        "error_hints": [],
        "id": "adca02a4-58eb-44b3-956f-b09aef7be02a",
        "last_message": "Manifest delivery completed",
        "last_modified": "2020-12-03T22:22:35.619Z",
        "name": "test_order",
        "products": [
            {
                "item_ids": [
                    "3949357_1454705_2020-12-01_241c"
                ],
                "item_type": "PSOrthoTile",
                "product_bundle": "analytic"
            }
        ],
        "state": "success"
    }
    return test_order


def test_Order_results(order_description):
    order = orders.Order(order_description)
    assert len(order.results) == 3


def test_Order_locations(order_description):
    order = orders.Order(order_description)
    expected_locations = ['location1', 'location2', 'location3']
    assert order.locations == expected_locations


@pytest.fixture
def test_order_details_dict():
    test_order_details = {
      "name": "string",
      "subscription_id": 0,
      "products": [
        {
          "item_ids": [
            "string"
          ],
          "item_type": "psorthotile",
          "product_bundle": "analytic"
        }
      ],
      "delivery": {
        "single_archive": True,
        "archive_type": "string",
        "archive_filename": "string",
        "layout": {
          "format": "standard"
        },
        "amazon_s3": {
          "bucket": "string",
          "aws_region": "string",
          "aws_access_key_id": "string",
          "aws_secret_access_key": "string",
          "path_prefix": "string"
        },
        "azure_blob_storage": {
          "account": "string",
          "container": "string",
          "sas_token": "string",
          "storage_endpoint_suffix": "string",
          "path_prefix": "string"
        },
        "google_cloud_storage": {
          "bucket": "string",
          "credentials": "string",
          "path_prefix": "string"
        },
        "google_earth_engine": {
          "project": "string",
          "collection": "string"
        }
      },
      "notifications": {
        "webhook": {
          "url": "string",
          "per_order": True
        },
        "email": True
      },
      "order_type": "full",
      "tools": [
        {
          "anchor_item": "string",
          "method": "string",
          "anchor_bundle": "string",
          "strict": True
        }
      ]
    }
    return test_order_details


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


def test_OrderDetails__validate_details_valid(test_order_details_dict):
    test_order_details_dict['products'][0]['product_bundle'] = 'ANALYTIC'
    test_order_details_dict['products'][0]['item_type'] = 'psorthotile'

    _ = orders.OrderDetails(test_order_details_dict)


def test_OrderDetails__validate_details_invalid(test_order_details_dict):
    invalid_bundle = test_order_details_dict.copy()
    invalid_bundle['products'][0]['product_bundle'] = 'nope'

    with pytest.raises(orders.OrderDetailsException):
        _ = orders.OrderDetails(invalid_bundle)

    invalid_item = test_order_details_dict.copy()
    invalid_item['products'][0]['product_bundle'] = 'ANALYTIC'
    invalid_item['products'][0]['item_type'] = 'nope'

    with pytest.raises(orders.OrderDetailsException):
        _ = orders.OrderDetails(invalid_item)
