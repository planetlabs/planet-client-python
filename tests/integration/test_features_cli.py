import tempfile
import json
import pytest

import respx
from click.testing import CliRunner

from planet.cli import cli
from tests.integration.test_features_api import TEST_COLLECTION_1, TEST_COLLECTION_LIST, TEST_FEAT, TEST_GEOM, TEST_URL, list_collections_response, list_features_response, mock_response, to_collection_model


def invoke(*args):

    runner = CliRunner()
    opts = ["--base-url", TEST_URL]
    args = ['features'] + opts + [arg for arg in args]

    result = runner.invoke(cli.main, args=args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


@respx.mock
def test_collection_list():

    collections_url = f'{TEST_URL}/collections'
    mock_response(collections_url,
                  list_collections_response(TEST_COLLECTION_LIST))

    def assertf(resp):
        assert resp[0]["id"] == "collection1"
        assert resp[1]["id"] == "collection2"

    assertf(invoke("collections", "list"))


@respx.mock
def test_get_collection():
    id = TEST_COLLECTION_1["id"]
    collection_url = f'{TEST_URL}/collections/{id}'

    mock_response(collection_url, to_collection_model(TEST_COLLECTION_1))

    def assertf(resp):
        assert resp["id"] == "collection1"
        assert resp["title"] == "Collection 1"

    assertf(invoke("collections", "get", id))


@respx.mock
def test_create_collection():

    collection_url = f'{TEST_URL}/collections'

    mock_response(collection_url,
                  to_collection_model(TEST_COLLECTION_1),
                  method='post')

    def assertf(resp):
        # the return value is simply the id.
        assert resp == "collection1"

    assertf(
        invoke("collections",
               "create",
               "--title",
               TEST_COLLECTION_1["title"],
               "--description",
               TEST_COLLECTION_1["description"]))

    req_body = json.loads(respx.calls[0].request.content)
    assert req_body["title"] == "Collection 1"
    assert req_body["description"] == "test collection 1"


@respx.mock
def test_list_items():
    collection_id = "test"
    items_url = f'{TEST_URL}/collections/{collection_id}/items'

    mock_response(items_url,
                  list_features_response(collection_id, num_features=3))

    def assertf(resp):
        assert resp[0]["id"] == "0"
        assert resp[1]["id"] == "1"

    assertf(invoke("items", "list", collection_id))


@respx.mock
@pytest.mark.parametrize("feature, expected_body", [
    (TEST_FEAT, TEST_GEOM),
    (TEST_GEOM, TEST_GEOM),
])
def test_add_items(feature, expected_body):
    """test adding a feature with the CLI
    cases:
    * a geojson Feature
    * a geojson Geometry
    """
    collection_id = "test"
    items_url = f'{TEST_URL}/collections/{collection_id}/items'

    # mock a feature ref return
    feat_resp = ["pl:features/my/test/test1"]
    mock_response(items_url, feat_resp, method="post")

    def assertf(resp):
        # check that mocked response is returned in full
        assert resp == feat_resp

    with tempfile.NamedTemporaryFile('w+') as file:
        json.dump(feature, file)
        file.flush()

        assertf(invoke("items", "add", collection_id, file.name))

        # check request body. In all test cases, the request body
        # should be a geojson Feature.
        req_body = json.loads(respx.calls[0].request.content)
        assert req_body["type"] == "Feature"
        assert req_body["geometry"] == expected_body
