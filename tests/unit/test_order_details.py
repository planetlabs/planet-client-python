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

from planet import geojson, specs
from planet.api import order_details

LOGGER = logging.getLogger(__name__)

TEST_ID = 'doesntmatter'
TEST_PRODUCT_BUNDLE = 'analytic_sr'
TEST_FALLBACK_BUNDLE = 'analytic'
TEST_ITEM_TYPE = 'PSOrthoTile'
TEST_ARCHIVE_FILENAME = '{{name}}_b_{order_id}}.zip'


def test_build_request():
    product = {
      "item_ids": [TEST_ID],
      "item_type": TEST_ITEM_TYPE,
      "product_bundle": f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }
    subscription_id = 5
    delivery = {
      'archive_type': 'zip',
      'single_archive': True,
      'archive_filename': TEST_ARCHIVE_FILENAME,
      'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            }
      }
    notifications = {
      'email': 'email',
      'webhook_url': 'webhookurl',
      'webhook_per_order': True
      }
    order_type = 'partial'
    tool = {'band_math': 'jsonstring'}

    request = order_details.build_request(
        'test_name',
        [product],
        subscription_id=subscription_id,
        delivery=delivery,
        notifications=notifications,
        order_type=order_type,
        tools=[tool]
        )
    expected = {
        'name': 'test_name',
        'products': [product],
        'subscription_id': subscription_id,
        'delivery': delivery,
        'notifications': notifications,
        'order_type': order_type,
        'tools': [tool]
    }
    assert request == expected

    order_type = 'notsupported'
    with pytest.raises(specs.SpecificationException):
        _ = order_details.build_request(
            'test_name',
            [product],
            subscription_id=subscription_id,
            delivery=delivery,
            notifications=notifications,
            order_type=order_type,
            tools=[tool]
            )


def test_product():
    product_config = order_details.product(
        [TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE,
        fallback_bundle=TEST_FALLBACK_BUNDLE)

    expected = {
      "item_ids": [TEST_ID],
      "item_type": TEST_ITEM_TYPE,
      "product_bundle": f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }
    assert product_config == expected

    with pytest.raises(specs.SpecificationException):
        _ = order_details.product([TEST_ID],
                                  'notsupported',
                                  TEST_ITEM_TYPE,
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_details.product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  'notsupported',
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_details.product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  TEST_ITEM_TYPE,
                                  fallback_bundle='notsupported')


def test_notifications():
    notifications_config = order_details.notifications(
        email='email',
        webhook_url='webhookurl',
        webhook_per_order=True
    )
    expected = {
      'email': 'email',
      'webhook_url': 'webhookurl',
      'webhook_per_order': True
      }
    assert notifications_config == expected

    empty_notifications_config = order_details.notifications(
    )
    empty_expected = {}
    assert empty_notifications_config == empty_expected


def test_delivery():
    as3_config = {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            }
    }
    delivery_config = order_details.delivery(
        'zip',
        True,
        TEST_ARCHIVE_FILENAME,
        cloud_config=as3_config
    )

    expected = {
      'archive_type': 'zip',
      'single_archive': True,
      'archive_filename': TEST_ARCHIVE_FILENAME,
      'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            }
      }
    assert delivery_config == expected


def test_amazon_s3():
    as3_config = order_details.amazon_s3(
        'aws_access_key_id',
        'aws_secret_access_key',
        'bucket',
        'aws_region'
    )
    expected = {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            }
    }
    assert as3_config == expected


def test_azure_blob_storage():
    abs_config = order_details.azure_blob_storage(
        'account',
        'container',
        'sas_token'
    )
    expected = {
        'azure_blob_storage': {
            'account': 'account',
            'container': 'container',
            'sas_token': 'sas_token',
            }
    }
    assert abs_config == expected


def test_google_cloud_storage():
    gcs_config = order_details.google_cloud_storage(
        'bucket',
        'credentials'
    )

    expected = {
        'google_cloud_storage': {
            'bucket': 'bucket',
            'credentials': 'credentials',
            }
    }
    assert gcs_config == expected


def test_google_earth_engine():
    gee_config = order_details.google_earth_engine('project', 'collection')
    expected = {
        'google_earth_engine': {
            'project': 'project',
            'collection': 'collection',
            }
    }

    assert gee_config == expected


def test__tool():
    test_tool = order_details._tool('band_math', 'jsonstring')
    assert test_tool == {'band_math': 'jsonstring'}

    with pytest.raises(specs.SpecificationException):
        _ = order_details._tool('notsupported', 'jsonstring')


def test_clip_tool(geom_geojson, point_geom_geojson):
    ct = order_details.clip_tool(geom_geojson)
    expected = {
        'clip': {
            'aoi': geom_geojson
        }}
    assert ct == expected

    with pytest.raises(geojson.WrongTypeException):
        _ = order_details.clip_tool(point_geom_geojson)


def test_reproject_tool():
    rt = order_details.reproject_tool(
        projection='proj',
        resolution=5
    )
    expected = {
        'reproject': {
            'projection': 'proj',
            'resolution': 5
            }
        }
    assert rt == expected


def test_tile_tool():
    tt = order_details.tile_tool(
        30,
        pixel_size=3
    )
    expected = {
        'tile': {
            'tile_size': 30,
            'pixel_size': 3
        }
    }
    assert tt == expected


def test_toar_tool():
    tt = order_details.toar_tool(
        scale_factor=5
    )
    expected = {
        'toar': {
            'scale_factor': 5
            }
    }
    assert tt == expected

    tt_empty = order_details.toar_tool()
    expected_empty = {
        'toar': {}
    }
    assert tt_empty == expected_empty
