# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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

from planet import exceptions, order_request, specs

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
        'email': 'email', 'webhook': {
            'url': 'webhookurl', 'per_order': True
        }
    }
    order_type = 'partial'
    tool = {'bandmath': 'jsonstring'}
    stac_json = {'stac': {}}

    request = order_request.build_request('test_name', [product],
                                          subscription_id=subscription_id,
                                          delivery=delivery,
                                          notifications=notifications,
                                          order_type=order_type,
                                          tools=[tool],
                                          stac=stac_json)
    expected = {
        'name': 'test_name',
        'products': [product],
        'subscription_id': subscription_id,
        'delivery': delivery,
        'notifications': notifications,
        'order_type': order_type,
        'tools': [tool],
        'metadata': stac_json
    }
    assert request == expected

    order_type = 'notsupported'
    with pytest.raises(specs.SpecificationException):
        _ = order_request.build_request('test_name', [product],
                                        subscription_id=subscription_id,
                                        delivery=delivery,
                                        notifications=notifications,
                                        order_type=order_type,
                                        tools=[tool],
                                        stac=stac_json)


def test_product():
    product_config = order_request.product(
        [TEST_ID],
        TEST_PRODUCT_BUNDLE,
        TEST_ITEM_TYPE,
        fallback_bundle=TEST_FALLBACK_BUNDLE)

    expected = {
        "item_ids": [TEST_ID],
        "item_type": TEST_ITEM_TYPE,
        "product_bundle": f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
    }
    assert product_config == expected

    with pytest.raises(specs.SpecificationException):
        _ = order_request.product([TEST_ID],
                                  'notsupported',
                                  TEST_ITEM_TYPE,
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_request.product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  'notsupported',
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_request.product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  TEST_ITEM_TYPE,
                                  fallback_bundle='notsupported')


def test_notifications():
    notifications_config = order_request.notifications(
        email=True, webhook_url='webhookurl', webhook_per_order=True)
    expected = {
        'email': True, 'webhook': {
            'url': 'webhookurl', 'per_order': True
        }
    }
    assert notifications_config == expected

    empty_notifications_config = order_request.notifications()
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
    delivery_config = order_request.delivery('zip',
                                             True,
                                             TEST_ARCHIVE_FILENAME,
                                             cloud_config=as3_config)

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


def test_delivery_missing_archive_details():
    as3_config = {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
        }
    }
    delivery_config = order_request.delivery(archive_type='zip',
                                             cloud_config=as3_config)

    expected = {
        'archive_type': 'zip',
        'archive_filename': "{{name}}_{{order_id}}.zip",
        'single_archive': False,
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
        }
    }
    assert delivery_config == expected


def test_amazon_s3():
    as3_config = order_request.amazon_s3('aws_access_key_id',
                                         'aws_secret_access_key',
                                         'bucket',
                                         'aws_region')
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
    abs_config = order_request.azure_blob_storage('account',
                                                  'container',
                                                  'sas_token')
    expected = {
        'azure_blob_storage': {
            'account': 'account',
            'container': 'container',
            'sas_token': 'sas_token',
        }
    }
    assert abs_config == expected


def test_google_cloud_storage():
    gcs_config = order_request.google_cloud_storage('bucket', 'credentials')

    expected = {
        'google_cloud_storage': {
            'bucket': 'bucket',
            'credentials': 'credentials',
        }
    }
    assert gcs_config == expected


def test_google_earth_engine():
    gee_config = order_request.google_earth_engine('project', 'collection')
    expected = {
        'google_earth_engine': {
            'project': 'project',
            'collection': 'collection',
        }
    }

    assert gee_config == expected


def test__tool():
    test_tool = order_request._tool('bandmath', 'jsonstring')
    assert test_tool == {'bandmath': 'jsonstring'}

    with pytest.raises(specs.SpecificationException):
        _ = order_request._tool('notsupported', 'jsonstring')


def test_clip_tool_polygon(geom_geojson):
    ct = order_request.clip_tool(geom_geojson)
    expected = {'clip': {'aoi': geom_geojson}}
    assert ct == expected


def test_clip_tool_multipolygon(multipolygon_geom_geojson):
    ct = order_request.clip_tool(multipolygon_geom_geojson)
    expected = {'clip': {'aoi': multipolygon_geom_geojson}}
    assert ct == expected


def test_clip_tool_invalid(point_geom_geojson):
    """Confirm an exception is raised if an invalid geometry type is supplied.
    """
    with pytest.raises(exceptions.ClientError):
        order_request.clip_tool(point_geom_geojson)


def test_reproject_tool():
    rt = order_request.reproject_tool(projection='proj', resolution=5)
    expected = {'reproject': {'projection': 'proj', 'resolution': 5}}
    assert rt == expected


def test_tile_tool():
    tt = order_request.tile_tool(30, pixel_size=3)
    expected = {'tile': {'tile_size': 30, 'pixel_size': 3}}
    assert tt == expected


def test_toar_tool():
    tt = order_request.toar_tool(scale_factor=5)
    expected = {'toar': {'scale_factor': 5}}
    assert tt == expected

    tt_empty = order_request.toar_tool()
    expected_empty = {'toar': {}}
    assert tt_empty == expected_empty


def test_harmonization_tool_success():
    ht = order_request.harmonize_tool("Sentinel-2")
    expected = {'harmonize': {'target_sensor': "Sentinel-2"}}
    assert ht == expected


def test_harmonization_tool_invalid_target_sensor():
    with pytest.raises(exceptions.ClientError):
        order_request.harmonize_tool('invalid')


def test_band_math_tool_success():
    res = order_request.band_math_tool(b1='b1', b2='arctan(b1)')

    expected = {
        "bandmath": {
            "b1": "b1",
            "b2": "arctan(b1)",
            "pixel_type": specs.BAND_MATH_PIXEL_TYPE_DEFAULT
        }
    }
    assert res == expected


def test_band_math_tool_invalid_pixel_type():
    with pytest.raises(exceptions.ClientError):
        order_request.band_math_tool(b1='b1',
                                     b2='arctan(b1)',
                                     pixel_type="invalid")


def test_no_archive_items_without_type():
    """Without an archive type no filename or single option are passed."""
    delivery_config = order_request.delivery(
        None, True, TEST_ARCHIVE_FILENAME, cloud_config={"bogus_storage": {}})

    assert "bogus_storage" in delivery_config
    assert "archive_type" not in delivery_config
    assert "archive_filename" not in delivery_config
    assert "single_archive" not in delivery_config


def test_sentinel_hub():
    sh_config = order_request.sentinel_hub()
    expected = {'sentinel_hub': {}}
    assert sh_config == expected


def test_sentinel_hub_collection_id():
    sh_config = order_request.sentinel_hub("1234")
    expected = {'sentinel_hub': {'collection_id': "1234"}}
    assert sh_config == expected
