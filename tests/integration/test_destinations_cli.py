# Copyright 2025 Planet Labs PBC.
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
"""Test Destinations CLI"""
import pytest
import respx
import httpx
from http import HTTPStatus
from click.testing import CliRunner

from planet.cli import cli

TEST_DESTINATIONS_URL = 'https://api.planet.com/destinations/v1'


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = ['destinations'] + extra_args
        return runner.invoke(cli.main, args=args)

    return _invoke


@respx.mock
def test_destinations_cli_archive(invoke):
    url = f"{TEST_DESTINATIONS_URL}/fake-dest-id"
    respx.patch(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['archive', 'fake-dest-id'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_create(invoke):
    respx.post(TEST_DESTINATIONS_URL).return_value = httpx.Response(
        HTTPStatus.ACCEPTED, json={})

    # azure
    result = invoke([
        'create',
        'azure',
        '--container',
        'my-container',
        '--account',
        'mystorage',
        '--sas-token',
        '?sv=...',
        '--storage-endpoint-suffix',
        'core.windows.net',
        '--name',
        'my-azure-destination'
    ])
    assert result.exit_code == 0

    # gcs
    result = invoke([
        'create',
        'gcs',
        '--bucket',
        'my-bucket',
        '--credentials',
        'eyJ0eXAiOiJKV1Qi...',
        '--name',
        'my-gcs-destination'
    ])
    assert result.exit_code == 0

    # ocs
    result = invoke([
        'create',
        'ocs',
        '--bucket',
        'my-bucket',
        '--access-key-id',
        'OCID...',
        '--secret-access-key',
        'SECRET...',
        '--namespace',
        'my-namespace',
        '--region',
        'us-ashburn-1',
        '--name',
        'my-ocs-destination'
    ])
    assert result.exit_code == 0

    # s3
    result = invoke([
        'create',
        's3',
        '--bucket',
        'my-bucket',
        '--region',
        'us-west-2',
        '--access-key-id',
        'AKIA...',
        '--secret-access-key',
        'SECRET...',
        '--explicit-sse',
        '--name',
        'my-s3-destination'
    ])
    assert result.exit_code == 0

    # s3-compatible
    result = invoke([
        'create',
        's3-compatible',
        '--bucket',
        'my-bucket',
        '--endpoint',
        'https://objects.example.com',
        '--region',
        'us-east-1',
        '--access-key-id',
        'AKIA...',
        '--secret-access-key',
        'SECRET...',
        '--use-path-style',
        '--name',
        'my-s3-comp-destination'
    ])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_get(invoke):
    url = f"{TEST_DESTINATIONS_URL}/fake-dest-id"
    respx.get(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['get', 'fake-dest-id'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_rename(invoke):
    url = f"{TEST_DESTINATIONS_URL}/fake-dest-id"
    respx.patch(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['rename', 'fake-dest-id', 'new-name'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_unarchive(invoke):
    url = f"{TEST_DESTINATIONS_URL}/fake-dest-id"
    respx.patch(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['unarchive', 'fake-dest-id'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_list(invoke):
    respx.get(TEST_DESTINATIONS_URL).return_value = httpx.Response(
        HTTPStatus.OK, json={})

    result = invoke(['list'])
    assert result.exit_code == 0

    result = invoke(['list', '--archived', 'true'])
    assert result.exit_code == 0

    result = invoke(['list', '--is-owner', 'true'])
    assert result.exit_code == 0

    result = invoke(['list', '--can-write', 'true'])
    assert result.exit_code == 0

    result = invoke(['list', '--is-default', 'true'])
    assert result.exit_code == 0

    result = invoke(['list', '--archived', 'false'])
    assert result.exit_code == 0

    result = invoke(['list', '--is-owner', 'false'])
    assert result.exit_code == 0

    result = invoke(['list', '--can-write', 'false'])
    assert result.exit_code == 0

    result = invoke(['list', '--is-default', 'false'])
    assert result.exit_code == 0

    result = invoke(['list', '--archived', 'false', '--is-owner', 'true'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_update(invoke):
    url = f"{TEST_DESTINATIONS_URL}/fake-dest-id"
    respx.patch(url).return_value = httpx.Response(HTTPStatus.ACCEPTED,
                                                   json={})

    # azure
    result = invoke(
        ['update', 'azure', 'fake-dest-id', '--sas-token', '?sv=...'])
    assert result.exit_code == 0

    # gcs
    result = invoke([
        'update',
        'gcs',
        'fake-dest-id',
        '--credentials',
        'eyJ0eXAiOiJKV1Qi...'
    ])
    assert result.exit_code == 0

    # ocs
    result = invoke([
        'update',
        'ocs',
        'fake-dest-id',
        '--access-key-id',
        'OCID...',
        '--secret-access-key',
        'SECRET...'
    ])
    assert result.exit_code == 0

    # s3
    result = invoke([
        'update',
        's3',
        'fake-dest-id',
        '--access-key-id',
        'AKIA...',
        '--secret-access-key',
        'SECRET...',
        '--explicit-sse'
    ])
    assert result.exit_code == 0

    # s3-compatible
    result = invoke([
        'update',
        's3-compatible',
        'fake-dest-id',
        '--access-key-id',
        'AKIA...',
        '--secret-access-key',
        'SECRET...',
        '--use-path-style'
    ])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_default_set(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.put(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['default', 'set', 'fake-dest-id'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_default_set_bad_request(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.put(url).return_value = httpx.Response(
        HTTPStatus.BAD_REQUEST,
        json={
            "code": 400, "message": "Bad Request: Invalid destination ID"
        })

    result = invoke(['default', 'set', 'invalid-dest-id'])
    assert result.exit_code != 0
    assert "Failed to set default destination" in result.output


@respx.mock
def test_destinations_cli_default_get(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.get(url).return_value = httpx.Response(HTTPStatus.OK, json={})

    result = invoke(['default', 'get'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_default_get_not_found(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.get(url).return_value = httpx.Response(
        HTTPStatus.NOT_FOUND,
        json={
            "code": 404, "message": "No default destination configured"
        })

    result = invoke(['default', 'get'])
    assert result.exit_code != 0
    assert "Failed to get default destination" in result.output


@respx.mock
def test_destinations_cli_default_unset(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.delete(url).return_value = httpx.Response(HTTPStatus.NO_CONTENT)

    result = invoke(['default', 'unset'])
    assert result.exit_code == 0


@respx.mock
def test_destinations_cli_default_unset_unauthorized(invoke):
    url = f"{TEST_DESTINATIONS_URL}/default"
    respx.delete(url).return_value = httpx.Response(
        HTTPStatus.UNAUTHORIZED,
        json={
            "code": 401, "message": "Unauthorized: Insufficient permissions"
        })

    result = invoke(['default', 'unset'])
    assert result.exit_code != 0
    assert "Failed to unset default destination" in result.output
