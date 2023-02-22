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
