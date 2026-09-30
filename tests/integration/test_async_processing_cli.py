# Copyright 2026 Planet Labs PBC.
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
"""Tests of the planet async-processing CLI."""
import base64
from http import HTTPStatus
import json

import httpx
import pytest
import respx
from click.testing import CliRunner

from planet.cli import cli

from tests.integration.test_async_processing_api import (
    NOT_FOUND,
    PROCESS_URL,
    REQUEST,
    REQUEST_ID,
    RUNNING,
    TEST_URL,
)

REQUIRED = [
    "--collection",
    "sentinel-2-l2a",
    "--bbox",
    "1,2,3,4",
    "--width",
    "10",
    "--height",
    "10",
    "--delivery",
    "s3://b/p",
    "--iam-role-arn",
    "arn",
]


def invoke(*args, input=None, base_url=TEST_URL):
    runner = CliRunner()
    group = ["async-processing"]
    if base_url:
        group += ["--base-url", base_url]
    return runner.invoke(cli.main, args=group + list(args), input=input)


@pytest.fixture
def evalscript(tmp_path):
    path = tmp_path / "script.js"
    path.write_text("//VERSION=3")
    return str(path)


def test_help_lists_commands():
    result = invoke("--help", base_url=None)
    assert result.exit_code == 0
    for cmd in ("request", "create", "get", "wait"):
        assert cmd in result.output


@pytest.mark.parametrize("cmd", ["request", "create", "get", "wait"])
def test_subcommand_help_has_example(cmd):
    result = invoke(cmd, "--help", base_url=None)
    assert result.exit_code == 0
    assert "Example:" in result.output


def test_request_minimal(evalscript):
    result = invoke("request", *REQUIRED, "--evalscript", evalscript)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "input": {
            "bounds": {
                "bbox": [1.0, 2.0, 3.0, 4.0]
            },
            "data": [{
                "type": "sentinel-2-l2a"
            }]
        },
        "output": {
            "width": 10,
            "height": 10,
            "responses": [{
                "identifier": "default", "format": {
                    "type": "image/tiff"
                }
            }],
            "delivery": {
                "s3": {
                    "url": "s3://b/p", "iamRoleARN": "arn"
                }
            }
        },
        "evalscript": "//VERSION=3"
    }


def test_request_full(evalscript):
    geom = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Point", "coordinates": [1, 2]
        }
    }
    result = invoke("request",
                    "--collection",
                    "sentinel-2-l2a",
                    "--time-from",
                    "2024-01-01T00:00:00Z",
                    "--time-to",
                    "2024-02-01T00:00:00Z",
                    "--max-cloud-coverage",
                    "20",
                    "--mosaicking-order",
                    "leastCC",
                    "--geometry",
                    json.dumps(geom),
                    "--crs",
                    "http://www.opengis.net/def/crs/EPSG/0/4326",
                    "--resx",
                    "10",
                    "--resy",
                    "10",
                    "--response",
                    "default:image/tiff",
                    "--response",
                    "userdata:application/json",
                    "--delivery",
                    "s3://b/<REQUEST_ID>/<OUTPUT>",
                    "--aws-access-key-id",
                    "a",
                    "--aws-secret-access-key",
                    "s",
                    "--aws-region",
                    "us-east-1",
                    "--evalscript",
                    evalscript)
    assert result.exit_code == 0, result.output
    req = json.loads(result.output)
    assert req["input"]["bounds"] == {
        "geometry": {
            "type": "Point", "coordinates": [1, 2]
        },
        "properties": {
            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
        }
    }
    assert req["input"]["data"][0]["dataFilter"] == {
        "timeRange": {
            "from": "2024-01-01T00:00:00Z", "to": "2024-02-01T00:00:00Z"
        },
        "maxCloudCoverage": 20.0,
        "mosaickingOrder": "leastCC"
    }
    assert req["output"]["resx"] == 10.0
    assert [r["identifier"]
            for r in req["output"]["responses"]] == ["default", "userdata"]
    assert req["output"]["delivery"] == {
        "s3": {
            "url": "s3://b/<REQUEST_ID>/<OUTPUT>",
            "accessKey": "a",
            "secretAccessKey": "s",
            "region": "us-east-1"
        }
    }


def test_request_gcs_and_evalscript_url(tmp_path):
    creds = tmp_path / "key.json"
    creds.write_bytes(b'{"type": "service_account"}')
    args = [a if a != "s3://b/p" else "gs://b/p" for a in REQUIRED]
    result = invoke("request",
                    *args,
                    "--evalscript-url",
                    "gs://b/script.js",
                    "--gcs-credentials",
                    str(creds))
    assert result.exit_code == 0, result.output
    req = json.loads(result.output)
    expected = base64.b64encode(creds.read_bytes()).decode()
    assert req["output"]["delivery"] == {
        "gs": {
            "url": "gs://b/p", "credentials": expected
        }
    }
    assert req["evalscriptReference"] == {
        "gs": {
            "url": "gs://b/script.js", "credentials": expected
        }
    }
    assert "evalscript" not in req


@pytest.mark.parametrize(
    "extra, message",
    [
        ([], "exactly one of --evalscript and --evalscript-url"),
        (["--evalscript-url", "s3://b/e.js", "--evalscript", "EVALSCRIPT"],
         "exactly one of --evalscript and --evalscript-url"),
        (["--evalscript", "EVALSCRIPT", "--response", "default"],
         "IDENTIFIER:FORMAT"),
        (["--evalscript", "EVALSCRIPT", "--response", "default:image/gif"],
         "IDENTIFIER:FORMAT"),
        (["--evalscript", "EVALSCRIPT", "--resx", "10", "--resy", "10"],
         "not both"),
    ])
def test_request_invalid(evalscript, extra, message):
    extra = [evalscript if a == "EVALSCRIPT" else a for a in extra]
    result = invoke("request", *REQUIRED, *extra)
    assert result.exit_code != 0
    assert message in result.output


def test_request_gcs_requires_credentials(evalscript):
    args = [a if a != "s3://b/p" else "gs://b/p" for a in REQUIRED]
    result = invoke("request", *args, "--evalscript", evalscript)
    assert result.exit_code != 0
    assert "--gcs-credentials is required" in result.output


def test_request_s3_requires_credentials(evalscript):
    args = REQUIRED[:-2]
    result = invoke("request", *args, "--evalscript", evalscript)
    assert result.exit_code != 0
    assert "iam_role_arn" in result.output


@respx.mock
def test_create():
    respx.post(PROCESS_URL).return_value = httpx.Response(HTTPStatus.OK,
                                                          json=RUNNING)
    result = invoke("create", json.dumps(REQUEST))
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == RUNNING
    assert json.loads(respx.calls.last.request.content) == REQUEST


@respx.mock
def test_create_stdin():
    respx.post(PROCESS_URL).return_value = httpx.Response(HTTPStatus.OK,
                                                          json=RUNNING)
    result = invoke("create", "-", input=json.dumps(REQUEST))
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == RUNNING


@respx.mock
def test_create_bad_request():
    respx.post(PROCESS_URL).return_value = httpx.Response(
        HTTPStatus.BAD_REQUEST, json={"error": {
            "message": "bad bbox"
        }})
    result = invoke("create", json.dumps(REQUEST))
    assert result.exit_code == 1
    assert "bad bbox" in result.output


@respx.mock
def test_get():
    respx.get(f"{PROCESS_URL}/{REQUEST_ID}").return_value = httpx.Response(
        HTTPStatus.OK, json=RUNNING)
    result = invoke("get", REQUEST_ID)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == RUNNING


@respx.mock
def test_get_finished():
    respx.get(f"{PROCESS_URL}/{REQUEST_ID}").return_value = httpx.Response(
        HTTPStatus.NOT_FOUND, json=NOT_FOUND)
    result = invoke("get", REQUEST_ID)
    assert result.exit_code == 1
    assert "is not running" in result.output
    assert "error.json" in result.output


@respx.mock
def test_wait():
    route = respx.get(f"{PROCESS_URL}/{REQUEST_ID}")
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=RUNNING),
        httpx.Response(HTTPStatus.NOT_FOUND, json=NOT_FOUND),
    ]
    result = invoke("wait", REQUEST_ID, "--delay", "0")
    assert result.exit_code == 0, result.output
    assert f"{REQUEST_ID}: RUNNING" in result.output
    assert "is not running" in result.output
    assert route.call_count == 2


@respx.mock
def test_wait_max_attempts():
    respx.get(f"{PROCESS_URL}/{REQUEST_ID}").return_value = httpx.Response(
        HTTPStatus.OK, json=RUNNING)
    result = invoke("wait", REQUEST_ID, "--delay", "0", "--max-attempts", "1")
    assert result.exit_code == 1
    assert "still running" in result.output


@pytest.mark.parametrize(
    "deployment, host",
    [
        ("aws-eu-central-1", "services.sentinel-hub.com"),
        ("aws-us-west-2", "services-uswest2.sentinel-hub.com"),
    ])
@respx.mock
def test_deployment_selects_host(deployment, host):
    route = respx.get(f"https://{host}/async/v1/process/{REQUEST_ID}").mock(
        return_value=httpx.Response(HTTPStatus.OK, json=RUNNING))
    result = invoke("--deployment",
                    deployment,
                    "get",
                    REQUEST_ID,
                    base_url=None)
    assert result.exit_code == 0, result.output
    assert route.called
