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

from http import HTTPStatus
import pytest
import respx
import httpx

from planet import DestinationsClient, Session
from planet.auth import Auth
from planet.sync.destinations import DestinationsAPI

pytestmark = pytest.mark.anyio

TEST_URL = "http://test.planet.com/destinations/v1"

DEST_1_REQ_PAYLOAD = {
    "name": "Destination 1",
    "type": "amazon_s3",
    "parameters": {
        "bucket": "bucket3",
        "aws_region": "us-west-2",
        "aws_access_key_id": "key3",
        "aws_secret_access_key": "secret3"
    }
}

DEST_1 = {
    "id": "dest1",
    "name": DEST_1_REQ_PAYLOAD["name"],
    "type": DEST_1_REQ_PAYLOAD["type"],
    "parameters": DEST_1_REQ_PAYLOAD["parameters"],
    "created": "2024-01-01T00:00:00Z",
    "updated": "2024-01-01T00:00:00Z",
    "pl:ref": "ref",
    "_links": {
        "_self": "url"
    },
    "archived": None,
    "permissions": {
        "can_write": True
    },
    "ownership": {
        "is_owner": True, "owner_id": 1
    }
}

DEST_2_PATCH_PAYLOAD = {
    "parameters": {
        "bucket": "bucket2", "credentials": "{}"
    }, "archive": True
}

DEST_2 = {
    "id": "dest2",
    "name": "Destination 2",
    "type": "google_cloud_storage",
    "parameters": {
        "bucket": "bucket2", "credentials": "{}"
    },
    "created": "2024-01-01T00:00:00Z",
    "updated": "2024-01-01T00:00:00Z",
    "pl:ref": "ref",
    "_links": {
        "_self": "url"
    },
    "archived": "2024-01-02T00:00:00Z",
    "permissions": {
        "can_write": True
    },
    "ownership": {
        "is_owner": True, "owner_id": 2
    }
}

DEST_LIST = [DEST_1, DEST_2]

test_session = Session(auth=Auth.from_key(key="test"))
cl_async = DestinationsClient(test_session, base_url=TEST_URL)
cl_sync = DestinationsAPI(test_session, base_url=TEST_URL)


def mock_response(url: str,
                  json_data,
                  method: str = "get",
                  status_code: int = HTTPStatus.OK):
    mock_resp = httpx.Response(status_code, json=json_data)
    respx.request(method, url).return_value = mock_resp


def construct_list_response(destinations):
    return {"destinations": destinations, "_links": {"_self": "url"}}


@respx.mock
async def test_list_destinations():
    mock_response(TEST_URL, construct_list_response(DEST_LIST))

    def assertf(resp):
        assert resp == construct_list_response(DEST_LIST)

    assertf(await cl_async.list_destinations())
    assertf(cl_sync.list_destinations())


@respx.mock
async def test_list_destinations_filtering():
    mock_response(f"{TEST_URL}?archived=false&is_owner=true",
                  construct_list_response([DEST_1]))

    def assertf(resp):
        assert resp == construct_list_response([DEST_1])

    assertf(await cl_async.list_destinations(archived=False, is_owner=True))
    assertf(cl_sync.list_destinations(archived=False, is_owner=True))


@respx.mock
async def test_get_destination():
    id = DEST_1["id"]
    url = f"{TEST_URL}/{id}"
    mock_response(url, DEST_1)

    def assertf(resp):
        assert resp == DEST_1

    assertf(await cl_async.get_destination(id))
    assertf(cl_sync.get_destination(id))


@respx.mock
async def test_create_destination():
    mock_response(TEST_URL,
                  DEST_1,
                  method="post",
                  status_code=HTTPStatus.CREATED)

    def assertf(resp):
        assert resp == DEST_1

    assertf(await cl_async.create_destination(DEST_1_REQ_PAYLOAD))
    assertf(cl_sync.create_destination(DEST_1_REQ_PAYLOAD))


@respx.mock
async def test_patch_destination():
    id = DEST_2["id"]
    url = f"{TEST_URL}/{id}"
    mock_response(url, DEST_2, method="patch")

    def assertf(resp):
        assert resp == DEST_2

    assertf(await cl_async.patch_destination(id, DEST_2_PATCH_PAYLOAD))
    assertf(cl_sync.patch_destination(id, DEST_2_PATCH_PAYLOAD))


@respx.mock
async def test_get_destination_not_found():
    id = "notfound"
    url = f"{TEST_URL}/{id}"
    mock_response(url, {
        "code": 404, "message": "Not found"
    },
                  status_code=HTTPStatus.NOT_FOUND)

    with pytest.raises(Exception):
        await cl_async.get_destination(id)
    with pytest.raises(Exception):
        cl_sync.get_destination(id)
