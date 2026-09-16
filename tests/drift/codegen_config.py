# Copyright 2024 Planet Labs PBC.
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
"""Single source of truth for the Pydantic model codegen invocation.

Both `nox -s generate_models` and the drift test import this module. The drift
test byte-compares regenerated output against the committed models, so the two
must build an identical command line from an identical version of
datamodel-code-generator (pinned in the `validate_models` extra).
"""
import json
import pathlib
import urllib.request

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
MODELS_DIR = REPO_ROOT / "planet" / "api_models"

# TODO: extend to other APIs as Pydantic models are adopted:
#   "subscriptions": "https://api.planet.com/subscriptions/v1/spec",
#   "orders":        "https://api.planet.com/compute/ops/spec",
#   "data":          "https://api.planet.com/data/v1/spec",
SPECS = {
    "destinations": "https://api.planet.com/destinations/v1/spec",
}

HEADER = ("# flake8: noqa\n"
          "# fmt: off\n"
          "# Generated code — do not edit manually.\n"
          "# Reformatting this file will break `nox -s validate_models`.\n"
          "# To regenerate, run:\n"
          "#   nox -s generate_models")

# Schema names whose anyOf blocks are pure required-field constraints
# (each entry has only a `required` key, no properties of its own).
# These exist solely to express "at least one of these fields must be set",
# which is a server-side validation rule. datamodel-codegen cannot represent
# that constraint cleanly: it generates N numbered classes (e.g.
# DestinationPatchRequest1/2/3) that are otherwise identical except for which
# field is marked required.
#
# We drop the anyOf during codegen so the generator emits a single, flat model
# with all fields optional. The constraint is still enforced server-side; the
# client SDK's job is to build and send the request, not to duplicate server
# validation in a way that produces unreadable generated names.
_DROP_CONSTRAINT_ANY_OF: set[str] = {
    "DestinationPatchRequest",
}


def fetch_and_patch_spec(url: str) -> dict:
    """Fetch an OpenAPI spec and strip pure-constraint anyOf blocks.

    Some schemas use ``anyOf`` exclusively to express "at least one of these
    fields must be present", using inline objects that each carry only a
    ``required`` key.  datamodel-codegen cannot name these inline schemas and
    falls back to numbered suffixes (``DestinationPatchRequest1``, etc.).

    This function removes those anyOf blocks before codegen so the generator
    produces a single, flat model.  The constraint is server-enforced; the
    client SDK does not need to replicate it.
    """
    with urllib.request.urlopen(url) as resp:
        spec = json.loads(resp.read())

    schemas = spec.get("components", {}).get("schemas", {})
    for schema_name in _DROP_CONSTRAINT_ANY_OF:
        schema = schemas.get(schema_name)
        if schema is None:
            continue
        # Only drop anyOf entries that are pure required-field constraints
        # (no properties of their own). If an entry has properties it is a
        # real subtype and must be kept.
        cleaned = [
            entry for entry in schema.get("anyOf", [])
            if "properties" in entry or "$ref" in entry
        ]
        if cleaned:
            schema["anyOf"] = cleaned
        else:
            schema.pop("anyOf", None)

    return spec


def codegen_argv(input_file: pathlib.Path, output: pathlib.Path) -> list:
    """Build the datamodel-codegen command line for one spec."""
    return [
        "datamodel-codegen",
        "--input",
        str(input_file),
        "--input-file-type",
        "openapi",
        "--output",
        str(output),
        "--output-model-type",
        "pydantic_v2.BaseModel",
        # Responses must tolerate fields Planet adds to the API. Without this,
        # an additive server change raises ValidationError in a shipped SDK.
        "--extra-fields",
        "allow",
        # Express constraints as Annotated[str, Field(max_length=...)] rather
        # than constr(...), which mypy rejects as an annotation in the modules
        # that import these models.
        "--use-annotated",
        # Pinned, not inferred from the interpreter running codegen: output
        # differs between Python versions, which would fail the drift check.
        # 3.10 is the project's requires-python floor.
        "--target-python-version",
        "3.10",
        # The spec is OpenAPI 3.0.3 and marks fields such as Destination.archived
        # as both required and `nullable: true`. Without this, codegen drops the
        # nullability and the model rejects the null the API actually returns.
        "--strict-nullable",
        # Honour schema-level defaults on required fields (e.g. Destination.default
        # defaults to false), which the API omits rather than sending explicitly.
        "--use-default",
        "--custom-file-header",
        HEADER,
        "--formatters",
        "builtin",
    ]
