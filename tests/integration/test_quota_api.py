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
"""Tests of the Planet Quota Reservations API client."""
from http import HTTPStatus
import json
from typing import Any, Optional

import httpx
import pytest
import respx

from planet import QuotaClient, Session
from planet.auth import Auth
from planet.exceptions import APIError, ClientError
from planet.sync.quota import QuotaAPI

pytestmark = pytest.mark.anyio  # noqa

# Simulated host/path for testing purposes. Not a real subdomain.
TEST_URL = "http://test.planet.com/account/v1"
RESERVATIONS_URL = f"{TEST_URL}/quota-reservations/"
JOBS_URL = f"{TEST_URL}/quota-reservations/jobs"
PRODUCTS_URL = f"{TEST_URL}/my/products"

AOI_REF = "pl:features/my/test-collection/feature-1"

# Set up shared test clients (mirrors test_features_api.py).
test_session = Session(auth=Auth.from_key(key="test"))
cl_async = QuotaClient(test_session, base_url=TEST_URL)
cl_sync = QuotaAPI(test_session, base_url=TEST_URL)


def mock_response(url: str,
                  json: Any,
                  method: str = "get",
                  status_code: int = HTTPStatus.OK):
    """Register a single canned response on the respx router."""
    respx.request(method, url).return_value = httpx.Response(status_code,
                                                             json=json)


def _reservation(rid: int) -> dict:
    return {
        "id": rid,
        "aoi_ref": AOI_REF,
        "product_id": 100,
        "state": "active",
        "created_at": "2026-01-01T00:00:00Z",
    }


def _reservations_page(start: int,
                       end: int,
                       next_url: Optional[str] = None) -> dict:
    page: dict = {
        "meta": {
            "count": end - start
        },
        "results": [_reservation(i) for i in range(start, end)],
    }
    if next_url is not None:
        page["meta"]["next"] = next_url
    return page


def _job(jid: str = "job-abc") -> dict:
    return {
        "id": jid,
        "status": "complete",
        "processed_items": 2,
        "total_items": 2,
        "percentage": 100,
    }


# ---------------------------------------------------------------------------
# list_reservations
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_reservations_single_page():
    mock_response(RESERVATIONS_URL, _reservations_page(0, 3))

    def assertf(resp):
        assert [r["id"] for r in resp] == [0, 1, 2]

    assertf([r async for r in cl_async.list_reservations()])
    assertf(list(cl_sync.list_reservations()))


@respx.mock
async def test_list_reservations_paginated():
    """Follow the meta.next link until exhausted."""
    next_url = f"{RESERVATIONS_URL}?cursor=abc"
    # First page links to next_url, second page (matched via params) has no next.
    respx.get(RESERVATIONS_URL).mock(side_effect=[
        httpx.Response(200, json=_reservations_page(0, 2, next_url=next_url)),
        httpx.Response(200, json=_reservations_page(2, 4))
    ])

    items = [r async for r in cl_async.list_reservations()]
    assert [r["id"] for r in items] == [0, 1, 2, 3]


@respx.mock
async def test_list_reservations_respects_limit():
    # Two pages of two items each — limit=3 cuts iteration short.
    next_url = f"{RESERVATIONS_URL}?cursor=abc"
    respx.get(RESERVATIONS_URL).mock(side_effect=[
        httpx.Response(200, json=_reservations_page(0, 2, next_url=next_url)),
        httpx.Response(200, json=_reservations_page(2, 4))
    ])

    items = [r async for r in cl_async.list_reservations(limit=3)]
    assert [r["id"] for r in items] == [0, 1, 2]


@respx.mock
async def test_list_reservations_query_params():
    mock_response(RESERVATIONS_URL, _reservations_page(0, 1))

    _ = [
        r async for r in cl_async.list_reservations(
            fields="id,state",
            sort="-created_at",
            filters={
                "state": "active", "product_id__in": "1,2"
            },
            page_size=25,
        )
    ]

    sent = respx.calls[0].request.url.params
    assert sent["fields"] == "id,state"
    assert sent["sort"] == "-created_at"
    assert sent["state"] == "active"
    assert sent["product_id__in"] == "1,2"
    assert sent["limit"] == "25"


# ---------------------------------------------------------------------------
# get_reservation
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_reservation():
    rid = 42
    mock_response(f"{TEST_URL}/quota-reservations/{rid}", _reservation(rid))

    def assertf(resp):
        assert resp["id"] == rid

    assertf(await cl_async.get_reservation(rid))
    assertf(cl_sync.get_reservation(rid))


@respx.mock
async def test_get_reservation_api_error():
    rid = 99
    mock_response(f"{TEST_URL}/quota-reservations/{rid}",
                  json={"message": "not found"},
                  status_code=HTTPStatus.NOT_FOUND)
    with pytest.raises(APIError):
        await cl_async.get_reservation(rid)


# ---------------------------------------------------------------------------
# create_reservation
# ---------------------------------------------------------------------------


@respx.mock
async def test_create_reservation():
    payload = {
        "quota_total": 1000,
        "quota_used": 10,
        "quota_remaining": 990,
        "reservation_refs": ["pl:reservations/1"],
    }
    mock_response(RESERVATIONS_URL, payload, method="post")

    def assertf(resp):
        assert resp == payload

    assertf(await cl_async.create_reservation([AOI_REF], 100))
    assertf(cl_sync.create_reservation([AOI_REF], 100))

    req_body = json.loads(respx.calls[0].request.content)
    assert req_body == {"aoi_refs": [AOI_REF], "product_id": 100}


@respx.mock
async def test_create_reservation_with_collection_id():
    mock_response(RESERVATIONS_URL, {}, method="post")
    await cl_async.create_reservation([AOI_REF], 100, collection_id="col-1")
    req_body = json.loads(respx.calls[0].request.content)
    assert req_body["collection_id"] == "col-1"


@respx.mock
async def test_create_reservation_omits_collection_id_when_none():
    mock_response(RESERVATIONS_URL, {}, method="post")
    await cl_async.create_reservation([AOI_REF], 100)
    req_body = json.loads(respx.calls[0].request.content)
    assert "collection_id" not in req_body


# ---------------------------------------------------------------------------
# bulk_create_reservations
# ---------------------------------------------------------------------------


@respx.mock
async def test_bulk_create_reservations():
    bulk_url = f"{TEST_URL}/quota-reservations/bulk-reserve"
    payload = {"job_id": "job-abc", "status": "queued"}
    mock_response(bulk_url, payload, method="post")

    def assertf(resp):
        assert resp == payload

    assertf(await cl_async.bulk_create_reservations([AOI_REF], 100))
    assertf(cl_sync.bulk_create_reservations([AOI_REF], 100))

    req_body = json.loads(respx.calls[0].request.content)
    assert req_body == {"aoi_refs": [AOI_REF], "product_id": 100}


# ---------------------------------------------------------------------------
# estimate_reservation
# ---------------------------------------------------------------------------


@respx.mock
async def test_estimate_reservation():
    estimate_url = f"{TEST_URL}/quota-reservations/estimate"
    payload = {
        "total_cost": 5,
        "estimated_costs": [{
            "aoi_ref": AOI_REF, "cost": 5
        }],
        "quota_total": 100,
        "quota_remaining": 90,
        "quota_units": "sqkm",
    }
    mock_response(estimate_url, payload, method="post")

    def assertf(resp):
        assert resp == payload

    assertf(await cl_async.estimate_reservation([AOI_REF], 100, "col-1"))
    assertf(cl_sync.estimate_reservation([AOI_REF], 100, "col-1"))

    req_body = json.loads(respx.calls[0].request.content)
    assert req_body == {
        "aoi_refs": [AOI_REF],
        "product_id": 100,
        "collection_id": "col-1",
    }


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_jobs():
    page = {"meta": {"count": 2}, "results": [_job("a"), _job("b")]}
    mock_response(JOBS_URL, page)

    def assertf(resp):
        assert [j["id"] for j in resp] == ["a", "b"]

    assertf([j async for j in cl_async.list_jobs()])
    assertf(list(cl_sync.list_jobs()))


@respx.mock
async def test_get_job():
    job_id = "job-xyz"
    mock_response(f"{JOBS_URL}/{job_id}", _job(job_id))

    def assertf(resp):
        assert resp["id"] == job_id

    assertf(await cl_async.get_job(job_id))
    assertf(cl_sync.get_job(job_id))


async def test_get_job_empty_id_raises():
    with pytest.raises(ClientError):
        await cl_async.get_job("")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_products_list_payload():
    products = [
        {
            "id": 1, "supports_reservation": True
        },
        {
            "id": 2, "supports_reservation": False
        },
    ]
    mock_response(PRODUCTS_URL, products)

    def assertf(resp):
        assert [p["id"] for p in resp] == [1, 2]

    assertf(await cl_async.list_products())
    assertf(cl_sync.list_products())


@respx.mock
async def test_list_products_results_wrapper():
    """`/my/products` may wrap items in `results` — accept that shape too."""
    payload = {
        "results": [{
            "id": 7, "supports_reservation": True
        }],
    }
    mock_response(PRODUCTS_URL, payload)
    products = await cl_async.list_products()
    assert [p["id"] for p in products] == [7]


@respx.mock
async def test_list_products_products_wrapper():
    """And the `products` wrapper key is also tolerated."""
    payload = {
        "products": [{
            "id": 8, "supports_reservation": False
        }],
    }
    mock_response(PRODUCTS_URL, payload)
    products = await cl_async.list_products()
    assert [p["id"] for p in products] == [8]


@respx.mock
async def test_list_products_supports_reservation_filter():
    products = [
        {
            "id": 1, "supports_reservation": True
        },
        {
            "id": 2, "supports_reservation": False
        },
        {
            "id": 3, "supports_reservation": True
        },
    ]
    # Each filter invocation makes a fresh request — return the same list each time.
    respx.get(PRODUCTS_URL).mock(
        side_effect=lambda req: httpx.Response(200, json=products))

    supported = await cl_async.list_products(supports_reservation=True)
    assert [p["id"] for p in supported] == [1, 3]

    unsupported = await cl_async.list_products(supports_reservation=False)
    assert [p["id"] for p in unsupported] == [2]
