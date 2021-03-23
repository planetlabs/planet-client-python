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

from planet import specs
from planet.api import order_details

LOGGER = logging.getLogger(__name__)

TEST_ID = 'doesntmatter'
TEST_PRODUCT_BUNDLE = 'analytic_sr'
TEST_FALLBACK_BUNDLE = 'analytic'
TEST_ITEM_TYPE = 'PSOrthoTile'
TEST_ARCHIVE_FILENAME = '{{name}}_b_{order_id}}.zip'


def test_OrderDetails():
    test_product = order_details.Product(
            [TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE)
    _ = order_details.OrderDetails('test', [test_product])

    _ = order_details.OrderDetails(
        'test',
        [test_product],
        order_details.Delivery(archive_type='zip'),
        order_details.Notifications(email=True),
        [order_details.Tool('file_format', 'COG')]
    )


def test_OrderDetails_from_dict():
    min_details = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
    }
    _ = order_details.OrderDetails.from_dict(min_details)

    details = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
        'subscription_id': 1,
        'delivery': {'archive_type': 'zip'},
        'notifications': {'email': True},
        'tools': [
            {'file_format': 'COG'},
            {'toar': {'scale_factor': 10000}}
        ]
    }

    od = order_details.OrderDetails.from_dict(details)
    assert od.subscription_id == 1
    assert od.delivery.archive_type == 'zip'
    assert od.notifications.email
    assert od.tools[0].name == 'file_format'
    assert od.tools[0].parameters == 'COG'
    assert od.tools[1].name == 'toar'
    assert od.tools[1].parameters == {'scale_factor': 10000}


def test_OrderDetails_to_dict():
    test_product = order_details.Product(
            [TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE)

    od = order_details.OrderDetails(
        'test',
        [test_product],
        subscription_id=1,
        delivery=order_details.Delivery(archive_type='zip'),
        notifications=order_details.Notifications(email=True),
        tools=[order_details.Tool('file_format', 'COG')]
        )

    expected = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
        'subscription_id': 1,
        'delivery': {'archive_type': 'zip'},
        'notifications': {'email': True},
        'tools': [{'file_format': 'COG'}]
    }
    assert expected == od.to_dict()


def test_Product():
    _ = order_details.Product([TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE,
                              fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Product([TEST_ID],
                                  'notsupported',
                                  TEST_ITEM_TYPE,
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

        _ = order_details.Product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  'notsupported',
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

        _ = order_details.Product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  TEST_ITEM_TYPE,
                                  fallback_bundle='notsupported')


def test_Product_from_dict():
    test_details = {
      'item_ids': [TEST_ID],
      'item_type': TEST_ITEM_TYPE,
      'product_bundle': f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }

    p = order_details.Product.from_dict(test_details)
    assert p.item_ids == [TEST_ID]
    assert p.item_type == TEST_ITEM_TYPE
    assert p.product_bundle == TEST_PRODUCT_BUNDLE
    assert p.fallback_bundle == TEST_FALLBACK_BUNDLE


def test_Product_to_dict():
    p = order_details.Product([TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE,
                              fallback_bundle=TEST_FALLBACK_BUNDLE)
    p_dict = p.to_dict()

    expected = {
      "item_ids": [TEST_ID],
      "item_type": TEST_ITEM_TYPE,
      "product_bundle": f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }

    assert p_dict == expected


def test_Notifications_from_dict():
    test_details = {
      'email': 'email',
      'webhook_url': 'webhookurl',
      'webhook_per_order': True
      }

    n = order_details.Notifications.from_dict(test_details)
    assert n.email == 'email'
    assert n.webhook_url == 'webhookurl'
    assert n.webhook_per_order


def test_Notifications_to_dict():
    n = order_details.Notifications(email='email')
    assert n.to_dict() == {'email': 'email'}

    n = order_details.Notifications(webhook_url='webhookurl')
    assert n.to_dict() == {'webhook_url': 'webhookurl'}

    n = order_details.Notifications(webhook_per_order=True)
    assert n.to_dict() == {'webhook_per_order': True}


def test_Delivery():
    d = order_details.Delivery(archive_type='Zip')
    assert d.archive_type == 'zip'


def test_Delivery_from_dict():
    test_details = {
      'archive_type': 'zip',
      'single_archive': True,
      'archive_filename': TEST_ARCHIVE_FILENAME
      }

    d = order_details.Delivery.from_dict(test_details)
    assert d.archive_type == 'zip'
    assert d.single_archive
    assert d.archive_filename == TEST_ARCHIVE_FILENAME

    test_details_cloud = {
        'cloud': {'a': 'val'},
        'archive_type': 'zip',
        'single_archive': True,
        'archive_filename': TEST_ARCHIVE_FILENAME
    }

    class TestDelivery(order_details.Delivery):
        cloud_key = 'cloud'

        def __init__(self, a, archive_type, single_archive, archive_filename):
            self.a = a
            super().__init__(archive_type, single_archive, archive_filename)

    # does the dict get parsed correctly and do the values get sent to the
    # constructor?
    d2 = TestDelivery.from_dict(test_details_cloud)
    assert d2.a == 'val'


def test_Delivery_to_dict():
    d = order_details.Delivery(archive_type='zip',
                               single_archive=True,
                               archive_filename=TEST_ARCHIVE_FILENAME)
    details = d.to_dict()
    expected = {
      'archive_type': 'zip',
      'single_archive': True,
      'archive_filename': TEST_ARCHIVE_FILENAME
      }
    assert details == expected

    d = order_details.Delivery(archive_type='zip')
    details = d.to_dict()
    expected = {
      'archive_type': 'zip',
      }
    assert details == expected


def test_AmazonS3Delivery_to_dict():
    aws_access_key_id = 'keyid'
    aws_secret_access_key = 'accesskey'
    bucket = 'bucket'
    aws_region = 'awsregion'
    archive_type = 'zip'

    d = order_details.AmazonS3Delivery(
        aws_access_key_id,
        aws_secret_access_key,
        bucket,
        aws_region,
        archive_type=archive_type)
    details = d.to_dict()
    expected = {
        'amazon_s3': {
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'bucket': bucket,
            'aws_region': aws_region
        },
        'archive_type': archive_type
    }
    assert details == expected


def test_AzureBlobStorageDelivery_to_dict():
    account = 'account'
    container = 'container'
    sas_token = 'sas_token'
    archive_type = 'zip'

    d = order_details.AzureBlobStorageDelivery(
        account,
        container,
        sas_token,
        archive_type=archive_type)
    details = d.to_dict()
    expected = {
        'azure_blob_storage': {
            'account': account,
            'container': container,
            'sas_token': sas_token,
        },
        'archive_type': archive_type
    }
    assert details == expected


def test_GoogleCloudStorageDelivery_to_dict():
    bucket = 'bucket'
    credentials = 'credentials'
    archive_type = 'zip'

    d = order_details.GoogleCloudStorageDelivery(
        bucket,
        credentials,
        archive_type=archive_type)
    details = d.to_dict()
    expected = {
        'google_cloud_storage': {
            'bucket': bucket,
            'credentials': credentials,
        },
        'archive_type': archive_type
    }
    assert details == expected


def test_GoogleEarthEngineDelivery_to_dict():
    project = 'project'
    collection = 'collection'
    archive_type = 'zip'

    d = order_details.GoogleEarthEngineDelivery(
        project,
        collection,
        archive_type=archive_type)
    details = d.to_dict()
    expected = {
        'google_earth_engine': {
            'project': project,
            'collection': collection,
        },
        'archive_type': archive_type
    }
    assert details == expected


def test_Tool():
    _ = order_details.Tool('band_math', 'jsonstring')

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Tool('notsupported', 'jsonstring')


def test_Tool_from_dict():
    details = {
            'band_math': {'b1': 'b1+b2'}
    }
    tool = order_details.Tool.from_dict(details)
    assert tool.name == 'band_math'
    assert tool.parameters == {'b1': 'b1+b2'}

    with pytest.raises(order_details.ToolException):
        _ = order_details.Tool.from_dict({'name': 'val', 'oops': 'error'})


def test_Tool_to_dict():
    _ = order_details.Tool('band_math', 'jsonstring')

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Tool('notsupported', 'jsonstring')
