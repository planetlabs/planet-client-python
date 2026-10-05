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
"""Tests of the Planet Async Processing API client."""
from http import HTTPStatus
import json

import httpx
import pytest
import respx

from planet import AsyncProcessingClient, Planet, Session
from planet.auth import Auth
from planet.clients.async_processing import DEPLOYMENT_URLS
from planet.exceptions import (BadQuery,
                               ClientError,
                               MissingResource,
                               TooManyRequests)
from planet.sync.async_processing import AsyncProcessingAPI

pytestmark = pytest.mark.anyio  # noqa

# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.planet.com/async/v1"
PROCESS_URL = f"{TEST_URL}/process"

REQUEST_ID = "7d9a1c2e-0000-4000-8000-000000000000"
RUNNING = {"id": REQUEST_ID, "status": "RUNNING"}
NOT_FOUND = {"error": {"status": 404, "reason": "Not Found"}}

REQUEST = {
    "input": {
        "bounds": {
            "bbox": [1, 2, 3, 4]
        }, "data": [{
            "type": "sentinel-2-l2a"
        }]
    },
    "output": {
        "width": 10,
        "height": 10,
        "delivery": {
            "s3": {
                "url": "s3://b/p", "iamRoleARN": "arn"
            }
        }
    },
    "evalscript": "//VERSION=3",
}

test_session = Session(auth=Auth.from_key(key="test"))
cl_async = AsyncProcessingClient(test_session, base_url=TEST_URL)
cl_sync = AsyncProcessingAPI(test_session, base_url=TEST_URL)


def status_route():
    return respx.get(f"{PROCESS_URL}/{REQUEST_ID}")


EU_URL = "https://services.sentinel-hub.com/async/v1"
US_URL = "https://services-uswest2.sentinel-hub.com/async/v1"


def test_default_deployment():
    assert set(DEPLOYMENT_URLS) == {"aws-eu-central-1", "aws-us-west-2"}
    assert AsyncProcessingClient(test_session)._process_url == \
        f"{EU_URL}/process"


@pytest.mark.parametrize("deployment, url",
                         [("aws-eu-central-1", EU_URL),
                          ("aws-us-west-2", US_URL)])
def test_deployment(deployment, url):
    assert AsyncProcessingClient(test_session,
                                 deployment=deployment)._base_url == url
    assert AsyncProcessingAPI(test_session,
                              deployment=deployment)._client._base_url == url


def test_base_url_overrides_deployment():
    cl = AsyncProcessingClient(test_session,
                               deployment="aws-us-west-2",
                               base_url=TEST_URL)
    assert cl._base_url == TEST_URL


def test_positional_base_url():
    # Same (session, base_url) order as the other clients.
    assert AsyncProcessingClient(test_session, TEST_URL)._base_url == TEST_URL
    assert AsyncProcessingAPI(test_session,
                              TEST_URL)._client._base_url == TEST_URL


def test_unknown_deployment():
    with pytest.raises(ClientError, match="aws-eu-central-1, aws-us-west-2"):
        AsyncProcessingClient(test_session, deployment="aws-ap-south-1")


def test_session_client_lookup():
    assert isinstance(test_session.client("async_processing"),
                      AsyncProcessingClient)


def test_planet_sync_client_uses_sentinel_hub():
    pl = Planet(session=test_session, base_url="http://test.planet.com")
    assert pl.async_processing._client._base_url == EU_URL


def test_planet_sync_client_deployment():
    pl = Planet(session=test_session,
                async_processing_deployment="aws-us-west-2")
    assert pl.async_processing._client._base_url == US_URL


@respx.mock
async def test_create_request():
    respx.post(PROCESS_URL).return_value = httpx.Response(HTTPStatus.OK,
                                                          json=RUNNING)
    assert await cl_async.create_request(REQUEST) == RUNNING
    assert json.loads(respx.calls.last.request.content) == REQUEST


@respx.mock
def test_create_request_sync():
    respx.post(PROCESS_URL).return_value = httpx.Response(HTTPStatus.OK,
                                                          json=RUNNING)
    assert cl_sync.create_request(REQUEST) == RUNNING


@respx.mock
async def test_create_request_bad_request():
    respx.post(PROCESS_URL).return_value = httpx.Response(
        HTTPStatus.BAD_REQUEST, json={"error": {
            "message": "bad bbox"
        }})
    with pytest.raises(BadQuery):
        await cl_async.create_request(REQUEST)


@respx.mock
async def test_create_request_concurrency_limit():
    # The session retries 429s; make it give up at once.
    respx.post(PROCESS_URL).return_value = httpx.Response(
        HTTPStatus.TOO_MANY_REQUESTS, json={})
    sess = Session(auth=Auth.from_key(key="test"))
    sess.max_retries = 0
    cl = AsyncProcessingClient(sess, base_url=TEST_URL)
    with pytest.raises(TooManyRequests):
        await cl.create_request(REQUEST)


@respx.mock
async def test_get_request():
    status_route().return_value = httpx.Response(HTTPStatus.OK, json=RUNNING)
    assert await cl_async.get_request(REQUEST_ID) == RUNNING


@respx.mock
def test_get_request_sync():
    status_route().return_value = httpx.Response(HTTPStatus.OK, json=RUNNING)
    assert cl_sync.get_request(REQUEST_ID) == RUNNING


@respx.mock
async def test_get_request_finished():
    status_route().return_value = httpx.Response(HTTPStatus.NOT_FOUND,
                                                 json=NOT_FOUND)
    with pytest.raises(MissingResource):
        await cl_async.get_request(REQUEST_ID)


async def test_get_request_empty_id():
    with pytest.raises(ClientError):
        await cl_async.get_request("")


@respx.mock
async def test_wait():
    route = status_route()
    route.side_effect = [
        httpx.Response(HTTPStatus.OK, json=RUNNING),
        httpx.Response(HTTPStatus.OK, json=RUNNING),
        httpx.Response(HTTPStatus.NOT_FOUND, json=NOT_FOUND),
    ]
    seen = []
    assert await cl_async.wait(REQUEST_ID, delay=0,
                               callback=seen.append) is None
    assert seen == ["RUNNING", "RUNNING"]
    assert route.call_count == 3


@respx.mock
def test_wait_sync():
    status_route().side_effect = [
        httpx.Response(HTTPStatus.OK, json=RUNNING),
        httpx.Response(HTTPStatus.NOT_FOUND, json=NOT_FOUND),
    ]
    assert cl_sync.wait(REQUEST_ID, delay=0) is None


@respx.mock
async def test_wait_max_attempts():
    route = status_route()
    route.return_value = httpx.Response(HTTPStatus.OK, json=RUNNING)
    with pytest.raises(ClientError, match="still running"):
        await cl_async.wait(REQUEST_ID, delay=0, max_attempts=2)
    assert route.call_count == 2
