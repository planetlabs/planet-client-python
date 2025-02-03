# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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

from planet import quota_request

LOGGER = logging.getLogger(__name__)


def test_my_products():
    organization_id = 6789
    request = quota_request.build_my_products_request(organization_id)
    expected = {
        "meta": {
            "args": {
                "limit": 50, "offset": 0, "organization_id": organization_id
            },
            "count": 0,
            "next": "null",
            "prev": "null"
        },
        "results": [{
            "billable_id":
            "prn:usage-api:bucket:306cf963-334d-49b6-b2c8-346da95a2fbf",
            "created_at": "2024-04-15T10:57:40.251801",
            "id": 1234,
            "organization_id": organization_id,
            "product": {
                "description": "test",
                "name": "BMP_10M",
                "title": "Biomass Proxy 10m"
            },
            "quota_total": "null",
            "quota_used": 0.0,
            "term_end_date": "2029-01-01T23:59:59.999999",
            "term_start_date": "2023-01-01T00:00:00",
            "unlimited_quota": "false",
            "updated_at": "2024-04-15T10:57:40.251815"
        }]
    }

    assert request == expected


def test_my_products_empty():
    organization_id = 123
    request = quota_request.build_my_products_empty_request(organization_id)
    expected = {
        "meta": {
            "args": {
                "limit": 50, "offset": 0, "organization_id": organization_id
            },
            "count": 0,
            "next": "null",
            "prev": "null"
        },
        "results": []
    }

    assert request == expected


def test_get_quota_reservations():
    limit = 10
    sort = "created_at"
    request = quota_request.build_get_quota_reservations_request(limit, sort)
    expected = {
        "meta": {
            "args": {
                "limit": limit, "offset": 0, "sort": sort
            },
            "count": 1,
            "next": None,
            "prev": None
        },
        "results": [{
            "amount": 100,
            "aoi_ref": "aoi_123",
            "collection_id": "col_456",
            "created_at": "2024-04-15T10:57:40.251801",
            "id": 789,
            "organization_id": 6789,
            "product_id": 123,
            "state": "active",
            "updated_at": "2024-04-15T10:57:40.251815",
            "url": "https://api.planet.com/account/v1/quota-reservations/789",
            "user_id": 456
        }]
    }
    assert request == expected


def test_create_quota_reservations():
    payload = {
        "aoi_refs": ["string"], "collection_id": "string", "product_id": 0
    }
    aoi_refs = payload["aoi_refs"]
    product_id = payload["product_id"]
    request = quota_request.build_create_quota_reservations_request(
        aoi_refs, product_id)
    expected = {
        "quota_remaining":
        123456,
        "quota_reservations": [{
            "aoi_ref":
            "pl:features/my/migratory_budgerigar_areas-2zxYEZD/191522007976127-zGoijt3",
            "id": 78910,
            "quota_used": 98765,
            "state": "reserved"
        }],
        "quota_total":
        12324352345345,
        "quota_used":
        98765
    }
    assert request == expected


def test_estimate_quota_reservations():
    payload = {"aoi_refs": ["string"], "product_id": 0}
    aoi_refs = payload["aoi_refs"]
    product_id = payload["product_id"]
    request = quota_request.build_estimate_quota_reservations_request(
        aoi_refs, product_id)
    expected = {
        "estimated_costs": [{
            "aoi_ref": aoi_refs[0], "cost": 2000
        }],
        "quota_remaining": 8000,
        "total_cost": 2000
    }
    assert request == expected


def test_create_bulk_quota_reservations():
    payload = {"aoi_refs": ["string"], "product_id": 0}
    aoi_refs = payload["aoi_refs"]
    product_id = payload["product_id"]
    request = quota_request.build_create_bulk_quota_reservations_request(
        aoi_refs, product_id)
    expected = {"job_id": "1", "status": "pending"}
    assert request == expected
