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
"""Contract tests for the generated Destinations models.

These pin the two halves of the unknown-field policy set in
tests/drift/codegen_config.py. Request models reject unknown fields so a typo
fails client side. Response models accept them so an additive server change
does not break a shipped SDK.
"""
import pydantic
import pytest

from planet.api_models.destinations import (
    AmazonS3PatchParams,
    DefaultDestinationRequest,
    Destination,
    DestinationPatchRequest,
    DestinationRequest,
    DestinationsResponse,
)

DEST = {
    "id": "dest1",
    "name": "Destination 1",
    "type": "amazon_s3",
    "parameters": {
        "bucket": "bucket1",
        "aws_region": "us-west-2",
        "aws_access_key_id": "key1",
        "aws_secret_access_key": "secret1",
    },
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
    },
}

REQUEST_MODELS = [
    (DestinationRequest,
     {
         "type": "amazon_s3",
         "parameters": {
             "bucket": "bucket1",
             "aws_region": "us-west-2",
             "aws_access_key_id": "key1",
             "aws_secret_access_key": "secret1",
         },
     }),
    (DestinationPatchRequest, {
        "archive": True
    }),
    (DefaultDestinationRequest, {
        "destination_id": "dest1"
    }),
    (AmazonS3PatchParams, {
        "aws_access_key_id": "key1", "aws_secret_access_key": "secret1"
    }),
]


@pytest.mark.parametrize("model,payload", REQUEST_MODELS)
def test_request_model_accepts_valid_payload(model, payload):
    assert model.model_validate(payload)


@pytest.mark.parametrize("model,payload", REQUEST_MODELS)
def test_request_model_rejects_unknown_field(model, payload):
    """The spec marks these additionalProperties: false. Catch typos locally."""
    with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
        model.model_validate({**payload, "buckett": "typo"})


def test_response_model_tolerates_unknown_field():
    """An additive server change must not break a released SDK."""
    dest = Destination.model_validate({**DEST, "future_field": "value"})
    assert dest.id == "dest1"
    assert dest.future_field == "value"


def test_response_model_tolerates_unknown_nested_param():
    """Params are echoed in responses, so they tolerate extras too."""
    params = {**DEST["parameters"], "future_param": "value"}
    dest = Destination.model_validate({**DEST, "parameters": params})
    assert dest.parameters.root.future_param == "value"


def test_destinations_response_round_trips_aliases():
    """Serialization emits wire names, not Python field names."""
    response = DestinationsResponse.model_validate({
        "destinations": [DEST], "_links": {
            "_self": "url"
        }
    })
    dumped = response.model_dump(mode="json",
                                 by_alias=True,
                                 exclude_unset=True)

    assert "_links" in dumped
    assert dumped["destinations"][0]["pl:ref"] == "ref"
    assert dumped["destinations"][0]["created"].startswith("2024-01-01")
    assert "field_links" not in dumped["destinations"][0]
