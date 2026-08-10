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
"""Tests of the planet quota CLI."""
import json
import tempfile

import respx
from click.testing import CliRunner

from planet.cli import cli

from tests.integration.test_quota_api import (
    AOI_REF,
    JOBS_URL,
    PRODUCTS_URL,
    RESERVATIONS_URL,
    TEST_URL,
    _job,
    _reservation,
    _reservations_page,
    mock_response,
)


def invoke(*args, input=None):
    runner = CliRunner()
    full_args = ["quota", "--base-url", TEST_URL] + list(args)
    result = runner.invoke(cli.main, args=full_args, input=input)
    assert result.exit_code == 0, result.output
    return result


def _parse_json_lines(output: str):
    """`echo_json` prints one JSON document per line — parse them all."""
    return [json.loads(line) for line in output.splitlines() if line.strip()]


@respx.mock
def test_cli_products_list():
    products = [
        {
            "id": 1,
            "name": "PSScene",
            "title": "PlanetScope Scene",
            "supports_reservation": True,
            "quota_total": 10,
            "quota_used": 1,
            "unlimited_quota": False,
            "extra": "dropped-when-compact",
        },
        {
            "id": 2,
            "name": "OtherProduct",
            "supports_reservation": False,
            "quota_total": 0,
            "quota_used": 0,
            "unlimited_quota": True,
            "extra": "still-here-without-compact",
        },
    ]
    mock_response(PRODUCTS_URL, products)

    # Default: every key surfaces.
    result = invoke("products", "list")
    data = json.loads(result.output)
    assert [p["id"] for p in data] == [1, 2]
    assert data[0]["extra"] == "dropped-when-compact"


@respx.mock
def test_cli_products_list_compact():
    products = [
        {
            "id": 1,
            "name": "PSScene",
            "title": "PlanetScope Scene",
            "supports_reservation": True,
            "quota_total": 10,
            "quota_used": 1,
            "unlimited_quota": False,
            "extra": "dropped-when-compact",
        },
    ]
    mock_response(PRODUCTS_URL, products)

    result = invoke("products", "list", "--compact")
    data = json.loads(result.output)
    assert "extra" not in data[0]
    assert set(data[0].keys()) == {
        "id",
        "name",
        "title",
        "supports_reservation",
        "quota_total",
        "quota_used",
        "unlimited_quota",
    }


@respx.mock
def test_cli_products_list_supports_reservation_flag():
    products = [
        {
            "id": 1, "supports_reservation": True
        },
        {
            "id": 2, "supports_reservation": False
        },
    ]
    respx.get(PRODUCTS_URL).respond(json=products)

    result = invoke("products", "list", "--supports-reservation")
    assert [p["id"] for p in json.loads(result.output)] == [1]


@respx.mock
def test_cli_reservations_list():
    mock_response(RESERVATIONS_URL, _reservations_page(0, 3))
    result = invoke("reservations", "list")
    items = _parse_json_lines(result.output)
    assert [i["id"] for i in items] == [0, 1, 2]


@respx.mock
def test_cli_reservations_list_passes_filters():
    mock_response(RESERVATIONS_URL, _reservations_page(0, 1))
    invoke(
        "reservations",
        "list",
        "--limit",
        "5",
        "--sort",
        "-created_at",
        "--fields",
        "id,state",
        "--filter",
        "state=active",
        "--filter",
        "product_id__in=1,2",
        "--page-size",
        "50",
    )
    params = respx.calls[0].request.url.params
    assert params["sort"] == "-created_at"
    assert params["fields"] == "id,state"
    assert params["state"] == "active"
    assert params["product_id__in"] == "1,2"
    assert params["limit"] == "50"


def test_cli_reservations_list_bad_filter():
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        args=[
            "quota",
            "--base-url",
            TEST_URL,
            "reservations",
            "list",
            "--filter",
            "no_equals_sign",
        ],
    )
    assert result.exit_code != 0
    assert "--filter" in result.output


@respx.mock
def test_cli_reservations_get():
    rid = 42
    mock_response(f"{TEST_URL}/quota-reservations/{rid}", _reservation(rid))
    result = invoke("reservations", "get", str(rid))
    assert json.loads(result.output)["id"] == rid


@respx.mock
def test_cli_reservation_create_aoi_ref_flags():
    """Repeated --aoi-ref flags accumulate into a list."""
    payload = {"reservation_refs": ["pl:reservations/1"]}
    mock_response(RESERVATIONS_URL, payload, method="post")

    result = invoke(
        "reservations",
        "create",
        "--aoi-ref",
        AOI_REF,
        "--aoi-ref",
        "pl:features/my/c/f2",
        "--product-id",
        "100",
    )
    assert json.loads(result.output) == payload

    body = json.loads(respx.calls[0].request.content)
    assert body == {
        "aoi_refs": [AOI_REF, "pl:features/my/c/f2"],
        "product_id": 100,
    }


@respx.mock
def test_cli_reservation_create_aoi_refs_json_string():
    """`--aoi-refs '[...]'` passes a JSON array directly."""
    mock_response(RESERVATIONS_URL, {}, method="post")
    invoke(
        "reservations",
        "create",
        "--aoi-refs",
        json.dumps([AOI_REF]),
        "--product-id",
        "100",
        "--collection-id",
        "col-1",
    )

    body = json.loads(respx.calls[0].request.content)
    assert body == {
        "aoi_refs": [AOI_REF],
        "product_id": 100,
        "collection_id": "col-1",
    }


@respx.mock
def test_cli_reservation_create_aoi_refs_from_file():
    mock_response(RESERVATIONS_URL, {}, method="post")
    with tempfile.NamedTemporaryFile("w+", suffix=".json") as f:
        json.dump([AOI_REF, "pl:features/my/c/f2"], f)
        f.flush()
        invoke(
            "reservations",
            "create",
            "--aoi-refs",
            f.name,
            "--product-id",
            "100",
        )

    body = json.loads(respx.calls[0].request.content)
    assert body["aoi_refs"] == [AOI_REF, "pl:features/my/c/f2"]


@respx.mock
def test_cli_reservation_create_aoi_refs_from_stdin():
    mock_response(RESERVATIONS_URL, {}, method="post")
    invoke(
        "reservations",
        "create",
        "--aoi-refs",
        "-",
        "--product-id",
        "100",
        input=json.dumps([AOI_REF]),
    )
    body = json.loads(respx.calls[0].request.content)
    assert body["aoi_refs"] == [AOI_REF]


def test_cli_reservation_create_requires_aoi_refs():
    """Without --aoi-ref or --aoi-refs the command fails before any HTTP call."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        args=[
            "quota",
            "--base-url",
            TEST_URL,
            "reservations",
            "create",
            "--product-id",
            "100",
        ],
    )
    assert result.exit_code != 0
    assert "AOI ref" in result.output


@respx.mock
def test_cli_reservation_bulk_reserve():
    bulk_url = f"{TEST_URL}/quota-reservations/bulk-reserve"
    payload = {"job_id": "job-abc", "status": "queued"}
    mock_response(bulk_url, payload, method="post")

    result = invoke(
        "reservations",
        "bulk-reserve",
        "--aoi-ref",
        AOI_REF,
        "--product-id",
        "100",
    )
    assert json.loads(result.output) == payload


@respx.mock
def test_cli_reservation_estimate():
    estimate_url = f"{TEST_URL}/quota-reservations/estimate"
    payload = {"total_cost": 5, "quota_remaining": 95}
    mock_response(estimate_url, payload, method="post")

    result = invoke(
        "reservations",
        "estimate",
        "--aoi-ref",
        AOI_REF,
        "--product-id",
        "100",
    )
    assert json.loads(result.output) == payload


@respx.mock
def test_cli_jobs_list():
    page = {"meta": {"count": 2}, "results": [_job("a"), _job("b")]}
    mock_response(JOBS_URL, page)
    result = invoke("jobs", "list")
    items = _parse_json_lines(result.output)
    assert [j["id"] for j in items] == ["a", "b"]


@respx.mock
def test_cli_jobs_get():
    job_id = "job-xyz"
    mock_response(f"{JOBS_URL}/{job_id}", _job(job_id))
    result = invoke("jobs", "get", job_id)
    assert json.loads(result.output)["id"] == job_id
