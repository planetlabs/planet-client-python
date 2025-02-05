# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Test Quota CLI"""
import json
from http import HTTPStatus

from click.testing import CliRunner
import httpx
import pytest
import respx

from planet.cli.quota import quota

TEST_URL = 'https://api.planet.com/account/v1'


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = extra_args
        return runner.invoke(quota, args=args)

    return _invoke


@respx.mock
def test_get_my_products(invoke):
    mock_response = {
        "meta": {"count": 1},
        "products": [{"id": "product_1"}]
    }
    respx.get(f"{TEST_URL}/my/products").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['get-my-products', '--organization-id', '1', '--limit', '10'])

    assert json.loads(result.output) == mock_response

@respx.mock
def test_estimate_reservation(invoke):
    mock_response = {"estimate": "some_estimate"}
    respx.post(f"{TEST_URL}/quota-reservations/estimate").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['estimate-reservation', 'aoi_1', 'aoi_2', '1234', '5678'])
    assert json.loads(result.output) == mock_response

@respx.mock
def test_create_reservation(invoke):
    mock_response = {"reservation": "some_reservation"}
    respx.post(f"{TEST_URL}/quota-reservations/").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['create-reservation', 'aoi_1', 'aoi_2', '1234', '5678'])
    assert json.loads(result.output) == mock_response

@respx.mock
def test_get_reservations(invoke):
    mock_response = {
        "meta": {"count": 1},
        "reservations": [{"id": "reservation_1"}]
    }
    respx.get(f"{TEST_URL}/quota-reservations/").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['get-reservations', '--limit', '10'])
    assert json.loads(result.output) == mock_response

@respx.mock
def test_create_bulk_reservations(invoke):
    mock_response = {"job_details": "some_job_details"}
    respx.post(f"{TEST_URL}/quota-reservations/bulk-reserve").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['create-bulk-reservations', 'aoi_1', 'aoi_2', '1234', '5678'])
    assert json.loads(result.output) == mock_response

@respx.mock
def test_get_bulk_reservation_job(invoke):
    mock_response = {"job": "some_job"}
    respx.get(f"{TEST_URL}/quota-reservations/jobs/1234").mock(return_value=httpx.Response(HTTPStatus.OK, json=mock_response))

    result = invoke(['get-bulk-reservation-job', '1234'])
    assert json.loads(result.output) == mock_response