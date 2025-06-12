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
#
from http import HTTPStatus
import json
from typing import Any
import httpx
import pytest
import respx

from planet import FeaturesClient, Session
from planet.auth import Auth
from planet.sync.features import FeaturesAPI

pytestmark = pytest.mark.anyio  # noqa

# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.planet.com/features/v1/ogc/my"

TEST_GEOM = {"type": "Polygon", "coordinates": [[[]]]}

TEST_FEAT = {"type": "Feature", "geometry": TEST_GEOM}

TEST_COLLECTION_1 = {
    "id": "collection1",
    "title": "Collection 1",
    "description": "test collection 1",
}

TEST_COLLECTION_2 = {
    "id": "collection2",
    "title": "Collection 2",
    "description": "test collection 2",
}

TEST_COLLECTION_LIST = [TEST_COLLECTION_1, TEST_COLLECTION_2]

# set up test clients
test_session = Session(auth=Auth.from_key(key="test"))
cl_async = FeaturesClient(test_session, base_url=TEST_URL)
cl_sync = FeaturesAPI(test_session, base_url=TEST_URL)


class ExampleGeoInterface:

    @property
    def __geo_interface__(self) -> dict:
        return TEST_GEOM


def mock_response(url: str,
                  json: Any,
                  method: str = "get",
                  status_code: int = HTTPStatus.OK):
    mock_resp = httpx.Response(status_code, json=json)
    respx.request(method, url).return_value = mock_resp


def to_collection_model(collection: dict) -> dict:
    """create a collection model as it would appear in a Features API response"""
    id = collection.get("id")

    # define a couple of the longer values up front for formatting reasons
    link = f"https://api.planet.com/features/v0/ogc/my/collections/{id}/items"
    permissions = {"can_write": True, "shared": False, "is_owner": True}

    return {
        "id": id,
        "title": collection.get("title"),
        "description": collection.get("description"),
        "item_type": "feature",
        "extent": {
            "spatial": {
                "bbox": [[0, 0, 1, 1]]
            }
        },
        "links": [
            {
                "href": f"{TEST_URL}/collections/{id}",
                "rel": "self",
                "title": "This collection",
                "type": "application/json",
            },
            {
                "href": link,
                "rel": "features",
                "title": "Features",
                "type": "application/json",
            },
        ],
        "feature_count": 1,
        "area": 1,
        "title_property": "NAME_0",
        "description_property": "description",
        "permissions": permissions,
    }


def list_collections_response(collections: list[dict]) -> dict:
    """simulate a list collections response"""
    return {
        "numberMatched": len(collections),
        "links": [{
            "href": f"{TEST_URL}/collections",
            "rel": "self",
            "title": "This page of results",
        }],
        "collections": [
            to_collection_model(collection) for collection in collections
        ],
    }


def to_feature_model(id: str) -> dict:
    return {
        "type": "Feature",
        "id": id,
        "properties": {},
        "geometry": {
            "coordinates": [[
                [7.05322265625, 46.81509864599243],
                [7.580566406250001, 46.81509864599243],
                [7.580566406250001, 47.17477833929903],
                [7.05322265625, 47.17477833929903],
                [7.05322265625, 46.81509864599243],
            ]],
            "type": "Polygon",
        },
    }


def list_features_response(collection_id: str, num_features: int) -> dict:
    return {
        "type": "FeatureCollection",
        "numberMatched": num_features,
        "links": [{
            "href": f"https://api.planet.com/features/v0/ogc/my/collections/{collection_id}/items",
            "rel": "self",
            "title": "This page of results",
        }],
        "features": [to_feature_model(str(i)) for i in range(num_features)],
    }


@respx.mock
async def test_list_collections():

    collections_url = f"{TEST_URL}/collections"
    mock_response(
        collections_url,
        list_collections_response([TEST_COLLECTION_1, TEST_COLLECTION_2]),
    )

    def assertf(resp):
        assert resp[0]["id"] == "collection1"
        assert resp[1]["id"] == "collection2"

    assertf([col async for col in cl_async.list_collections()])
    assertf(list(cl_sync.list_collections()))


@respx.mock
async def test_get_collection():

    id = TEST_COLLECTION_1["id"]
    collection_url = f"{TEST_URL}/collections/{id}"

    mock_response(collection_url, to_collection_model(TEST_COLLECTION_1))

    def assertf(resp):
        assert resp["id"] == "collection1"
        assert resp["title"] == "Collection 1"

    assertf(await cl_async.get_collection(id))
    assertf(cl_sync.get_collection(id))


@respx.mock
async def test_create_collection():

    collection_url = f"{TEST_URL}/collections"

    mock_response(collection_url,
                  to_collection_model(TEST_COLLECTION_1),
                  method="post")

    def assertf(resp):
        # the return value is simply the id.
        assert resp == "collection1"

    params = {
        "title": TEST_COLLECTION_1["title"],
        "description": TEST_COLLECTION_1["description"],
    }

    assertf(await cl_async.create_collection(**params))
    assertf(cl_sync.create_collection(**params))

    req_body = json.loads(respx.calls[0].request.content)
    assert req_body["title"] == "Collection 1"
    assert req_body["description"] == "test collection 1"


@respx.mock
async def test_list_items():
    collection_id = "test"
    items_url = f"{TEST_URL}/collections/{collection_id}/items"

    mock_response(items_url,
                  list_features_response(collection_id, num_features=3))

    def assertf(resp):
        assert resp[0]["id"] == "0"
        assert resp[1]["id"] == "1"

    assertf([feat async for feat in cl_async.list_items(collection_id)])
    assertf(list(cl_sync.list_items(collection_id)))


@respx.mock
@pytest.mark.parametrize(
    "feature, expected_body",
    [
        (TEST_FEAT, TEST_GEOM),
        (TEST_GEOM, TEST_GEOM),
        (ExampleGeoInterface(), TEST_GEOM),
    ],
)
async def test_add_items(feature, expected_body):
    """test adding a feature with the SDK
    cases:
    * a geojson Feature
    * a geojson Geometry
    * an object that implements __geo_interface__
    """
    collection_id = "test"
    items_url = f"{TEST_URL}/collections/{collection_id}/items"

    # mock a feature ref return
    feat_resp = ["pl:features/my/test/test1"]
    mock_response(items_url, feat_resp, method="post")

    def assertf(resp):
        # check that mocked response is returned in full
        assert resp == feat_resp

    assertf(await cl_async.add_items(collection_id, feature))
    assertf(cl_sync.add_items(collection_id, feature))

    # check request body. In all test cases, the request body
    # should be a geojson Feature.
    req_body = json.loads(respx.calls[0].request.content)
    assert req_body["type"] == "Feature"
    assert req_body["geometry"] == expected_body


@respx.mock
async def test_get_item():
    collection_id = "test"
    item_id = "test123"
    items_url = f"{TEST_URL}/collections/{collection_id}/items/{item_id}"

    mock_response(items_url, to_feature_model(item_id))

    def assertf(resp):
        assert resp["id"] == item_id

    assertf(await cl_async.get_item(collection_id, item_id))
    assertf(cl_sync.get_item(collection_id, item_id))


@respx.mock
async def test_delete_item():
    collection_id = "test"
    item_id = "test123"
    items_url = f"{TEST_URL}/collections/{collection_id}/items/{item_id}"

    mock_response(items_url,
                  json=None,
                  method="delete",
                  status_code=HTTPStatus.NO_CONTENT)

    def assertf(resp):
        assert resp is None

    assertf(await cl_async.delete_item(collection_id, item_id))
    assertf(cl_sync.delete_item(collection_id, item_id))


@respx.mock
async def test_delete_collection():
    collection_id = "test"
    collections_url = f"{TEST_URL}/collections/{collection_id}"

    mock_response(collections_url,
                  json=None,
                  method="delete",
                  status_code=HTTPStatus.NO_CONTENT)

    def assertf(resp):
        assert resp is None

    assertf(await cl_async.delete_collection(collection_id))
    assertf(cl_sync.delete_collection(collection_id))
