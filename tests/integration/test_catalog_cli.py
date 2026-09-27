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
"""Tests of the planet catalog CLI."""
import json
from http import HTTPStatus

import httpx
import respx
from click.testing import CliRunner

from planet.cli import cli

from tests.integration.test_catalog_api import (
    BBOX,
    COLLECTION,
    COLLECTION_ID,
    COLLECTIONS_URL,
    CONFORMANCE,
    DATETIME,
    LANDING_PAGE,
    QUERYABLES,
    SEARCH_URL,
    TEST_URL,
    _item,
    _item_collection,
    _request_bodies,
    _request_params,
    mock_response,
)


def invoke(*args, input=None):
    runner = CliRunner()
    full_args = ["catalog", "--base-url", TEST_URL] + list(args)
    result = runner.invoke(cli.main, args=full_args, input=input)
    assert result.exit_code == 0, result.output
    return result


def _parse_json_lines(output: str):
    """`echo_json` prints one JSON document per line - parse them all."""
    return [json.loads(line) for line in output.splitlines() if line.strip()]


@respx.mock
def test_cli_landing_page():
    mock_response(TEST_URL, LANDING_PAGE)
    result = invoke("landing-page")
    assert json.loads(result.output) == LANDING_PAGE


@respx.mock
def test_cli_conformance():
    mock_response(f"{TEST_URL}/conformance", CONFORMANCE)
    result = invoke("conformance")
    assert json.loads(result.output) == CONFORMANCE


@respx.mock
def test_cli_collections_list():
    mock_response(COLLECTIONS_URL, {"collections": [COLLECTION], "links": []})
    result = invoke("collections", "list")
    assert json.loads(result.output) == [COLLECTION]


@respx.mock
def test_cli_collections_get():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}", COLLECTION)
    result = invoke("collections", "get", COLLECTION_ID)
    assert json.loads(result.output) == COLLECTION


@respx.mock
def test_cli_collections_queryables():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/queryables", QUERYABLES)
    result = invoke("collections", "queryables", COLLECTION_ID)
    assert json.loads(result.output) == QUERYABLES


@respx.mock
def test_cli_items_get():
    item = _item("item-1")
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}/items/item-1", item)
    result = invoke("items", "get", COLLECTION_ID, "item-1")
    assert json.loads(result.output) == item


@respx.mock
def test_cli_items_list():
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 3))

    result = invoke("items",
                    "list",
                    COLLECTION_ID,
                    "--bbox",
                    "13,45,14,46",
                    "--datetime",
                    DATETIME,
                    "--page-size",
                    "25")

    items = _parse_json_lines(result.output)
    assert [item["id"] for item in items] == ["item-0", "item-1", "item-2"]

    params = _request_params()
    assert params["bbox"] == "13.0,45.0,14.0,46.0"
    assert params["datetime"] == DATETIME
    assert params["limit"] == "25"


@respx.mock
def test_cli_items_list_respects_limit():
    items_url = f"{COLLECTIONS_URL}/{COLLECTION_ID}/items"
    mock_response(items_url, _item_collection(0, 10))

    result = invoke("items", "list", COLLECTION_ID, "--limit", "2")

    assert len(_parse_json_lines(result.output)) == 2


@respx.mock
def test_cli_simple_search():
    mock_response(SEARCH_URL, _item_collection(0, 2))

    result = invoke("simple-search",
                    "--collections",
                    COLLECTION_ID,
                    "--datetime",
                    DATETIME,
                    "--bbox",
                    "13,45,14,46",
                    "--filter",
                    "eo:cloud_cover>90",
                    "--fields",
                    "id,type,-geometry")

    items = _parse_json_lines(result.output)
    assert [item["id"] for item in items] == ["item-0", "item-1"]

    params = _request_params()
    assert params["collections"] == COLLECTION_ID
    assert params["filter"] == "eo:cloud_cover>90"
    assert params["fields"] == "id,type,-geometry"


@respx.mock
def test_cli_simple_search_distinct():
    page = {
        "type": "FeatureCollection",
        "features": ["2020-12-29", "2020-12-27"],
        "links": [],
        "context": {
            "returned": 2
        },
    }
    mock_response(SEARCH_URL, page)

    result = invoke("simple-search",
                    "--collections",
                    COLLECTION_ID,
                    "--datetime",
                    DATETIME,
                    "--distinct",
                    "date")

    assert _parse_json_lines(result.output) == ["2020-12-29", "2020-12-27"]
    assert _request_params()["distinct"] == "date"


@respx.mock
def test_cli_search_sends_post_body():
    mock_response(SEARCH_URL, _item_collection(0, 2), method="post")

    result = invoke("search",
                    "--collections",
                    f"{COLLECTION_ID},sentinel-2-l1c",
                    "--datetime",
                    DATETIME,
                    "--bbox",
                    "13,45,14,46",
                    "--ids",
                    "item-0,item-1",
                    "--filter",
                    "eo:cloud_cover>90",
                    "--filter-lang",
                    "cql2-text",
                    "--page-size",
                    "50")

    items = _parse_json_lines(result.output)
    assert [item["id"] for item in items] == ["item-0", "item-1"]

    body = _request_bodies()[0]
    assert body["collections"] == [COLLECTION_ID, "sentinel-2-l1c"]
    assert body["datetime"] == DATETIME
    assert body["bbox"] == BBOX
    assert body["ids"] == ["item-0", "item-1"]
    assert body["filter"] == "eo:cloud_cover>90"
    assert body["filter-lang"] == "cql2-text"
    assert body["limit"] == 50


@respx.mock
def test_cli_search_parses_cql2_json_filter():
    """With --filter-lang cql2-json the filter is sent as JSON, not a string."""
    mock_response(SEARCH_URL, _item_collection(0, 1), method="post")

    cql2 = {"op": ">", "args": [{"property": "eo:cloud_cover"}, 90]}
    invoke("search",
           "--collections",
           COLLECTION_ID,
           "--datetime",
           DATETIME,
           "--filter",
           json.dumps(cql2),
           "--filter-lang",
           "cql2-json")

    body = _request_bodies()[0]
    assert body["filter"] == cql2
    assert body["filter-lang"] == "cql2-json"


@respx.mock
def test_cli_search_fields_object():
    mock_response(SEARCH_URL, _item_collection(0, 1), method="post")

    fields = {"include": ["id", "bbox"], "exclude": ["geometry"]}
    invoke("search",
           "--collections",
           COLLECTION_ID,
           "--datetime",
           DATETIME,
           "--fields",
           json.dumps(fields))

    assert _request_bodies()[0]["fields"] == fields


@respx.mock
def test_cli_search_intersects():
    mock_response(SEARCH_URL, _item_collection(0, 1), method="post")

    geom = {"type": "Point", "coordinates": [13.0, 45.0]}
    invoke("search",
           "--collections",
           COLLECTION_ID,
           "--datetime",
           DATETIME,
           "--intersects",
           json.dumps(geom))

    assert _request_bodies()[0]["intersects"] == geom


@respx.mock
def test_cli_search_pages():
    respx.post(SEARCH_URL).side_effect = [
        httpx.Response(HTTPStatus.OK,
                       json=_item_collection(0, 2, next_token="2")),
        httpx.Response(HTTPStatus.OK, json=_item_collection(2, 3)),
    ]

    result = invoke("search",
                    "--collections",
                    COLLECTION_ID,
                    "--datetime",
                    DATETIME)

    items = _parse_json_lines(result.output)
    assert [item["id"] for item in items] == ["item-0", "item-1", "item-2"]


def test_cli_search_requires_collections_and_datetime():
    """The spec marks both as required; click should enforce that."""
    runner = CliRunner()
    result = runner.invoke(cli.main, args=["catalog", "search"])
    assert result.exit_code != 0
    assert "--collections" in result.output


@respx.mock
def test_cli_api_error_is_translated():
    mock_response(f"{COLLECTIONS_URL}/{COLLECTION_ID}", {"code": 404},
                  status_code=HTTPStatus.NOT_FOUND)

    runner = CliRunner()
    result = runner.invoke(cli.main,
                           args=[
                               "catalog",
                               "--base-url",
                               TEST_URL,
                               "collections",
                               "get",
                               COLLECTION_ID
                           ])

    assert result.exit_code != 0
