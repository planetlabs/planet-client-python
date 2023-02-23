# Copyright 2023 Planet Labs PBC.
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

from planet import exceptions, subscription_request

LOGGER = logging.getLogger(__name__)


def test_amazon_s3_success():
    res = subscription_request.amazon_s3(aws_access_key_id='keyid',
                                         aws_secret_access_key='accesskey',
                                         bucket='bucket',
                                         aws_region='region')

    assert res == {
        "delivery": {
            "type": "amazon_s3",
            "parameters": {
                "aws_access_key_id": "keyid",
                "aws_secret_access_key": "accesskey",
                "bucket": "bucket",
                "aws_region": "region"
            }
        }
    }


def test_azure_blob_storage_success():
    res = subscription_request.azure_blob_storage(
        account='act',
        container='container',
        sas_token='sastoken',
        storage_endpoint_suffix='suffix')

    assert res == {
        "delivery": {
            "type": "azure_blob_storage",
            "parameters": {
                "account": "act",
                "container": "container",
                "sas_token": "sastoken",
                "storage_endpoint_suffix": "suffix"
            }
        }
    }


def test_google_cloud_storage_success():
    res = subscription_request.google_cloud_storage(credentials='cred',
                                                    bucket='bucket')

    assert res == {
        "delivery": {
            "type": "google_cloud_storage",
            "parameters": {
                "bucket": "bucket", "credentials": "cred"
            }
        }
    }


def test_oracle_cloud_storage_success():
    res = subscription_request.oracle_cloud_storage(
        customer_access_key_id='keyid',
        customer_secret_key='secretkey',
        bucket='bucket',
        region='region',
        namespace='namespace')

    assert res == {
        "delivery": {
            "type": "oracle_cloud_storage",
            "parameters": {
                "customer_access_key_id": "keyid",
                "customer_secret_key": "secretkey",
                "bucket": "bucket",
                "region": "region",
                "namespace": "namespace"
            }
        }
    }


def test_notifications_success():
    topics = ['delivery.success']
    notifications_config = subscription_request.notifications(url='url',
                                                              topics=topics)

    expected = {"webhook": {"url": "url", "topics": topics}}
    assert notifications_config == expected


def test_notifications_invalid_topics():
    with pytest.raises(exceptions.ClientError):
        subscription_request.notifications(url='url', topics=['invalid'])


def test_band_math_tool_success():
    res = subscription_request.band_math_tool(b1='b1', b2='arctan(b1)')

    expected = {
        "type": "bandmath",
        "parameters": {
            "b1": "b1",
            "b2": "arctan(b1)",
            "pixel_type": subscription_request.BAND_MATH_PIXEL_TYPE_DEFAULT
        }
    }
    assert res == expected


def test_band_math_tool_invalid_pixel_type():
    with pytest.raises(exceptions.ClientError):
        subscription_request.band_math_tool(b1='b1',
                                            b2='arctan(b1)',
                                            pixel_type="invalid")


def test_clip_tool_success(geom_geojson):
    res = subscription_request.clip_tool(geom_geojson)

    expected = {"type": "clip", "parameters": {"aoi": geom_geojson}}
    assert res == expected


def test_clip_tool_invalid_type(point_geom_geojson):
    with pytest.raises(exceptions.ClientError):
        subscription_request.clip_tool(point_geom_geojson)


def test_file_format_tool_success():
    res = subscription_request.file_format_tool('COG')

    expected = {"type": "file_format", "parameters": {"format": "COG"}}
    assert res == expected


def test_file_format_tool_invalid_format():
    with pytest.raises(exceptions.ClientError):
        subscription_request.file_format_tool('invalid')


def test_harmonize_tool_success():
    res = subscription_request.harmonize_tool('PS2')

    expected = {"type": "harmonize", "parameters": {"target_sensor": "PS2"}}
    assert res == expected


def test_harmonize_tool_invalid_target_sensor():
    with pytest.raises(exceptions.ClientError):
        subscription_request.harmonize_tool('invalid')


def test_reproject_tool_success():
    res = subscription_request.reproject_tool('EPSG:4326',
                                              kernel='near',
                                              resolution=0.5)

    expected = {
        "type": "reproject",
        "parameters": {
            "projection": "EPSG:4326", "kernel": "near", "resolution": 0.5
        }
    }
    assert res == expected


def test_reproject_tool_invalid_kernel():
    with pytest.raises(exceptions.ClientError):
        subscription_request.reproject_tool('EPSG:4326',
                                            kernel='invalid',
                                            resolution=0.5)
