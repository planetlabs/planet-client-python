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
"""Tests of the Planet Catalog API client."""
from http import HTTPStatus
import json
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from planet import CatalogClient, Session
from planet.auth import Auth
from planet.exceptions import APIError, PagingError
from planet.sync.catalog import CatalogAPI

pytestmark = pytest.mark.anyio  # noqa

# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.catalog.com/catalog/v1"
COLLECTIONS_URL = f"{TEST_URL}/collections"
SEARCH_URL = f"{TEST_URL}/search"

COLLECTION_ID = "sentinel-2-l2a"
DATETIME = "2020-12-10T00:00:00Z/2020-12-30T00:00:00Z"
BBOX = [13.0, 45.0, 14.0, 46.0]

# Set up shared test clients (mirrors test_features_api.py).
test_session = Session(auth=Auth.from_key(key="test"))
cl_async = CatalogClient(test_session, base_url=TEST_URL)
cl_sync = CatalogAPI(test_session, base_url=TEST_URL)


def mock_response(url: str,
                  json: Any,
                  method: str = "get",
                  status_code: int = HTTPStatus.OK):
    """Register a single canned response on the respx router."""
    respx.request(method, url).return_value = httpx.Response(status_code,
                                                             json=json)


def _item(item_id: str) -> dict:
    return {
        "type": "Feature",
        "id": item_id,
        "collection": COLLECTION_ID,
        "bbox": BBOX,
        "properties": {
            "datetime": "2020-12-29T10:18:19Z", "eo:cloud_cover": 93.93
        },
    }


def _item_collection(start: int,
                     end: int,
                     next_url: Optional[str] = None,
                     next_token: Optional[str] = None) -> dict:
    """A STAC ItemCollection page.

    `next_url` adds a `rel: next` link (how the GET endpoints page) and
    `next_token` adds a `context.next` token (how POST /search pages).
    """
    page: dict = {
        "type": "FeatureCollection",
        "features": [_item(f"item-{i}") for i in range(start, end)],
        "links": [{
            "rel": "self", "href": SEARCH_URL
        }],
    }
    if next_url is not None:
        page["links"].append({"rel": "next", "href": next_url})
    page["context"] = {"limit": end - start, "returned": end - start}
    if next_token is not None:
        page["context"]["next"] = next_token
    return page


def _request_bodies() -> list:
    """The JSON bodies of every POST recorded by respx, in order."""
    return [
        json.loads(call.request.content) for call in respx.calls
        if call.request.method == "POST"
    ]


def _request_params(index: int = 0) -> dict:
    """The parsed query string of the nth recorded request."""
    query = urlparse(str(respx.calls[index].request.url)).query
    return {
        k: v[0]
        for k, v in parse_qs(query, keep_blank_values=True).items()
    }


LANDING_PAGE = {
    "type": "Catalog",
    "stac_version": "1.0.0",
    "id": "sentinel-hub",
    "conformsTo": ["https://api.stacspec.org/v1.0.0/core"],
    "links": [{
        "rel": "self", "href": TEST_URL
    }],
}

CONFORMANCE = {"conformsTo": ["https://api.stacspec.org/v1.0.0/core"]}

COLLECTION = {
    "type": "Collection",
    "id": COLLECTION_ID,
    "title": "Sentinel 2 L2A",
    "license": "proprietary",
}

QUERYABLES = {
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "type": "object",
    "properties": {
        "eo:cloud_cover": {
            "type": "number", "minimum": 0, "maximum": 100
        }
    },
    "additionalProperties": False,
}


@respx.mock
async def test_get_landing_page_async():
    mock_response(TEST_URL, LANDING_PAGE)
    assert await cl_async.get_landing_page() == LANDING_PAGE


@respx.mock
def test_get_landing_page_sync():
    mock_response(TEST_URL, LANDING_PAGE)
    assert cl_sync.get_landing_page() == LANDING_PAGE


@respx.mock
async def test_get_conformance_async():
    mock_response(f"{TEST_URL}/conformance", CONFORMANCE)
    assert await cl_async.get_conformance() == CONFORMANCE


@respx.mock
def test_get_conformance_sync():
    mock_response(f"{TEST_URL}/conformance", CONFORMANCE)
    assert cl_sync.get_conformance() == CONFORMANCE


@respx.mock
async def test_list_collections_unwraps_collections_key():
    mock_response(COLLECTIONS_URL, {"collections": [COLLECTION], "links": []})
    assert await cl_async.list_collections() == [COLLECTION]


@respx.mock
def test_list_collections_sync():
    mock_response(COLLECTIONS_URL, {"collections": [COLLECTION], "links": []})
    assert cl_sync.list_collections() == [COLLECTION]


@respx.mock
async def test_list_collections_missing_key_returns_empty():
    """A payload without a `collections` key yields an empty list, not a
    KeyError."""
    mock_response(COLLECTIONS_URL, {"links": []})
    assert await cl_async.list_collections() == []


@respx.mock
async def test_get_collection_async():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}", COLLECTION)
    assert await cl_async.get_collection(COLLECTION_ID) == COLLECTION


@respx.mock
def test_get_collection_sync():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}", COLLECTION)
    assert cl_sync.get_collection(COLLECTION_ID) == COLLECTION


@respx.mock
async def test_get_collection_queryables_async():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/queryables", QUERYABLES)
    result = await cl_async.get_collection_queryables(COLLECTION_ID)
    assert result == QUERYABLES


@respx.mock
def test_get_collection_queryables_sync():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/queryables", QUERYABLES)
    assert cl_sync.get_collection_queryables(COLLECTION_ID) == QUERYABLES


@respx.mock
async def test_get_item_async():
    item = _item("item-1")
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/items/item-1", item)
    assert await cl_async.get_item(COLLECTION_ID, "item-1") == item


@respx.mock
def test_get_item_sync():
    item = _item("item-1")
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/items/item-1", item)
    assert cl_sync.get_item(COLLECTION_ID, "item-1") == item


@respx.mock
async def test_list_items_serializes_params():
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 2))

    results = [
        item async for item in cl_async.list_items(
            COLLECTION_ID, bbox=BBOX, datetime=DATETIME, page_size=25)
    ]

    assert [item["id"] for item in results] == ["item-0", "item-1"]

    params = _request_params()
    # `explode: false` - the bbox is one comma-joined value, not repeated.
    assert params["bbox"] == "13.0,45.0,14.0,46.0"
    assert params["datetime"] == DATETIME
    # page_size is sent as the API's `limit`.
    assert params["limit"] == "25"


@respx.mock
async def test_list_items_omits_unset_params():
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 1))

    [item async for item in cl_async.list_items(COLLECTION_ID)]

    params = _request_params()
    assert "bbox" not in params
    assert "datetime" not in params


@respx.mock
async def test_list_items_follows_next_link():
    """GET endpoints page by following the `rel: next` link."""
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    page_2_url = f"{items_url}?next=1"

    respx.get(items_url, params={
        "limit": "100"
    }).return_value = httpx.Response(HTTPStatus.OK,
                                     json=_item_collection(
                                         0, 2, next_url=page_2_url))
    respx.get(items_url, params={
        "next": "1"
    }).return_value = httpx.Response(HTTPStatus.OK,
                                     json=_item_collection(2, 4))

    results = [item async for item in cl_async.list_items(COLLECTION_ID)]

    assert [item["id"]
            for item in results] == ["item-0", "item-1", "item-2", "item-3"]


@respx.mock
def test_list_items_sync():
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 3))

    results = list(cl_sync.list_items(COLLECTION_ID))

    assert [item["id"] for item in results] == ["item-0", "item-1", "item-2"]


@respx.mock
async def test_list_items_respects_limit():
    """`limit` caps the total number of items yielded, across pages."""
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 10))

    results = [
        item async for item in cl_async.list_items(COLLECTION_ID, limit=3)
    ]

    assert len(results) == 3


@respx.mock
async def test_simple_search_serializes_params():
    mock_response(SEARCH_URL, _item_collection(0, 1))

    [
        item async for item in cl_async.simple_search(
            collections=[COLLECTION_ID], datetime=DATETIME, bbox=BBOX,
            ids=["item-0", "item-1"], fields="id,type,-geometry",
            filter="eo:cloud_cover>90", distinct="date", page_size=50)
    ]

    params = _request_params()
    assert params["collections"] == COLLECTION_ID
    assert params["datetime"] == DATETIME
    assert params["bbox"] == "13.0,45.0,14.0,46.0"
    assert params["ids"] == "item-0,item-1"
    assert params["fields"] == "id,type,-geometry"
    assert params["filter"] == "eo:cloud_cover>90"
    assert params["distinct"] == "date"
    assert params["limit"] == "50"


@respx.mock
async def test_simple_search_encodes_intersects_as_json():
    geom = {"type": "Point", "coordinates": [13.0, 45.0]}
    mock_response(SEARCH_URL, _item_collection(0, 1))

    [
        item async for item in cl_async.simple_search(
            collections=[COLLECTION_ID], datetime=DATETIME, intersects=geom)
    ]

    assert json.loads(_request_params()["intersects"]) == geom


@respx.mock
def test_simple_search_sync():
    mock_response(SEARCH_URL, _item_collection(0, 2))

    results = list(
        cl_sync.simple_search(collections=[COLLECTION_ID], datetime=DATETIME))

    assert [item["id"] for item in results] == ["item-0", "item-1"]


@respx.mock
async def test_search_builds_body():
    mock_response(SEARCH_URL, _item_collection(0, 1), method="post")

    [
        item async for item in cl_async.search(
            collections=[COLLECTION_ID], datetime=DATETIME, bbox=BBOX,
            ids=["item-0"], fields={
                "include": ["id", "bbox"], "exclude": ["geometry"]
            }, filter={
                "op": ">", "args": [{
                    "property": "eo:cloud_cover"
                }, 90]
            }, filter_lang="cql2-json",
            filter_crs="http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            distinct="date", page_size=50)
    ]

    body = _request_bodies()[0]
    assert body["collections"] == [COLLECTION_ID]
    assert body["datetime"] == DATETIME
    # Unlike the GET variant, POST sends native JSON types.
    assert body["bbox"] == BBOX
    assert body["ids"] == ["item-0"]
    assert body["fields"] == {
        "include": ["id", "bbox"], "exclude": ["geometry"]
    }
    assert body["distinct"] == "date"
    assert body["limit"] == 50
    # The spec names these with hyphens, not underscores.
    assert body["filter-lang"] == "cql2-json"
    assert body["filter-crs"] == "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    assert "filter_lang" not in body
    assert "filter_crs" not in body


@respx.mock
async def test_search_omits_unset_fields():
    mock_response(SEARCH_URL, _item_collection(0, 1), method="post")

    [
        item async for item in cl_async.search(collections=[COLLECTION_ID],
                                               datetime=DATETIME)
    ]

    body = _request_bodies()[0]
    assert set(body) == {"collections", "datetime", "limit"}


@respx.mock
async def test_search_pages_with_context_next_token():
    """POST /search pages by re-sending the query with a `next` token."""
    respx.post(SEARCH_URL).side_effect = [
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(0, 2, next_token="2")),
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(2, 4, next_token="4")),
        httpx.Response(HTTPStatus.OK, json=_item_collection(4, 5)),
    ]

    results = [
        item async for item in cl_async.search(collections=[COLLECTION_ID],
                                               datetime=DATETIME, bbox=BBOX)
    ]

    assert [item["id"] for item in results
            ] == ["item-0", "item-1", "item-2", "item-3", "item-4"]

    bodies = _request_bodies()
    assert len(bodies) == 3
    # The first request carries no token; later ones repeat the original
    # query with `next` added.
    assert "next" not in bodies[0]
    assert bodies[1]["next"] == "2"
    assert bodies[2]["next"] == "4"
    assert bodies[2]["bbox"] == BBOX
    assert bodies[2]["collections"] == [COLLECTION_ID]


@respx.mock
async def test_search_respects_limit_and_stops_paging():
    respx.post(SEARCH_URL).side_effect = [
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(0, 2, next_token="2")),
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(2, 4, next_token="4")),
    ]

    results = [
        item async for item in cl_async.search(collections=[COLLECTION_ID],
                                               datetime=DATETIME, limit=3)
    ]

    assert len(results) == 3


@respx.mock
async def test_search_raises_on_page_cycle():
    """A server that echoes the same token must not loop forever."""
    respx.post(SEARCH_URL).side_effect = [
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(0, 2, next_token="2")),
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(2, 4, next_token="2")),
    ]

    with pytest.raises(PagingError):
        [
            item async for item in cl_async.search(collections=[COLLECTION_ID],
                                                   datetime=DATETIME, limit=0)
        ]


@respx.mock
async def test_search_distinct_yields_values():
    """With `distinct`, `features` holds property values rather than items."""
    page = {
        "type": "FeatureCollection",
        "features": ["2020-12-29", "2020-12-27"],
        "links": [],
        "context": {
            "returned": 2
        },
    }
    mock_response(SEARCH_URL, page, method="post")

    results = [
        item async for item in cl_async.search(
            collections=[COLLECTION_ID], datetime=DATETIME, distinct="date")
    ]

    assert results == ["2020-12-29", "2020-12-27"]


@respx.mock
def test_search_sync():
    mock_response(SEARCH_URL, _item_collection(0, 2), method="post")

    results = list(
        cl_sync.search(collections=[COLLECTION_ID], datetime=DATETIME))

    assert [item["id"] for item in results] == ["item-0", "item-1"]


async def _consume(result):
    """Await a coroutine, or drain an async iterator."""
    if hasattr(result, "__aiter__"):
        return [item async for item in result]
    return await result


@pytest.mark.parametrize(
    "url, method, call",
    [
        (TEST_URL, "get", lambda: cl_async.get_landing_page()),
        (f"{TEST_URL}/conformance", "get", lambda: cl_async.get_conformance()),
        (COLLECTIONS_URL, "get", lambda: cl_async.list_collections()),
        (f"{COLLECTIONS_URL}/{COLLECTION_ID}",
         "get", lambda: cl_async.get_collection(COLLECTION_ID)),
        (f"{COLLECTIONS_URL}/{COLLECTION_ID}/queryables",
         "get", lambda: cl_async.get_collection_queryables(COLLECTION_ID)),
        (f"{COLLECTIONS_URL}/{COLLECTION_ID}/items",
         "get", lambda: cl_async.list_items(COLLECTION_ID)),
        (f"{COLLECTIONS_URL}/{COLLECTION_ID}/items/item-1",
         "get", lambda: cl_async.get_item(COLLECTION_ID, "item-1")),
        (SEARCH_URL,
         "get", lambda: cl_async.simple_search([COLLECTION_ID], DATETIME)),
        (SEARCH_URL,
         "post", lambda: cl_async.search([COLLECTION_ID], DATETIME)),
    ])
@respx.mock
async def test_api_errors_propagate(url, method, call):
    """Every method surfaces a server error rather than swallowing it.

    This matters most for the iterating methods, where the request is made
    inside an async generator and the error has to travel out through the
    `async for`.
    """
    mock_response(url, {"code": 500},
                  method=method,
                  status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    with pytest.raises(APIError):
        await _consume(call())


def test_default_base_url_is_sentinel_hub():
    """The Catalog API is not hosted at api.planet.com."""
    from planet.clients.catalog import BASE_URL, US_WEST_2_BASE_URL

    assert BASE_URL == "https://services.sentinel-hub.com/catalog/v1"
    assert US_WEST_2_BASE_URL == (
        "https://services-uswest2.sentinel-hub.com/catalog/v1")
    assert CatalogClient(test_session)._base_url == BASE_URL


def test_base_url_trailing_slash_is_stripped():
    cl = CatalogClient(test_session, base_url=f"{TEST_URL}/")
    assert cl._base_url == TEST_URL
    assert cl._search_url == SEARCH_URL
