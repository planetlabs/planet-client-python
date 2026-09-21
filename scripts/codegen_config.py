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

Spec URLs, output paths and other settings live in codegen_constants.
"""
import json
import pathlib
import urllib.request

from codegen_constants import (
    DROP_CONSTRAINT_ANY_OF,
    HEADER,
    MODELS_DIR,
    REPO_ROOT,
    SPECS,
    TARGET_PYTHON_VERSION,
)

__all__ = [
    "MODELS_DIR",
    "REPO_ROOT",
    "SPECS",
    "codegen_argv",
    "fetch_and_patch_spec",
    "response_reachable_schemas",
]


def _schema_refs(node) -> list:
    """Collect every ``components/schemas`` name referenced under a node."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.append(value.rsplit("/", 1)[-1])
            else:
                found.extend(_schema_refs(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_schema_refs(value))
    return found


def response_reachable_schemas(spec: dict) -> set:
    """Names of schemas the API can return, followed transitively from responses.

    Everything else is request-only.  The two halves want opposite handling of
    unknown fields, so codegen needs to tell them apart.
    """
    schemas = spec.get("components", {}).get("schemas", {})

    pending = []
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                pending.extend(_schema_refs(operation.get("responses", {})))

    reachable: set = set()
    while pending:
        name = pending.pop()
        if name in reachable or name not in schemas:
            continue
        reachable.add(name)
        pending.extend(_schema_refs(schemas[name]))
    return reachable


def fetch_and_patch_spec(url: str) -> dict:
    """Fetch an OpenAPI spec and patch it for codegen.

    Two patches, both applied before datamodel-codegen sees the spec.

    1. Strip pure-constraint ``anyOf`` blocks.  Some schemas use ``anyOf``
       exclusively to express "at least one of these fields must be present",
       using inline objects that each carry only a ``required`` key.
       datamodel-codegen cannot name these inline schemas and falls back to
       numbered suffixes (``DestinationPatchRequest1``, etc.).  Removing the
       block yields a single, flat model.  The constraint is server-enforced;
       the client SDK does not need to replicate it.

    2. Relax ``additionalProperties`` on response schemas.  Codegen is run
       without a global ``--extra-fields`` override, so it honours the spec:
       ``additionalProperties: false`` becomes ``extra='forbid'``.  That is
       what we want for request models -- a typo'd key fails client side,
       before the round trip.  It is wrong for responses: a shipped SDK must
       not raise when Planet adds a field.  So every schema reachable from a
       response is forced to ``additionalProperties: true``, giving
       ``extra='allow'``.

    Note the overlap.  ``AmazonS3Params`` and its siblings appear in both
    requests and responses, so tolerance wins and they are generated as
    ``allow``.  Only ``*PatchParams`` and the top-level request bodies are
    request-only, and those get ``forbid``.
    """
    with urllib.request.urlopen(url) as resp:
        spec = json.loads(resp.read())

    schemas = spec.get("components", {}).get("schemas", {})
    for schema_name in DROP_CONSTRAINT_ANY_OF:
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

    for name in response_reachable_schemas(spec):
        schema = schemas[name]
        # Enums and unions (oneOf/anyOf roots) carry no properties of their
        # own; additionalProperties is meaningless there and confuses codegen.
        if "properties" in schema:
            schema["additionalProperties"] = True

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
        # Express constraints as Annotated[str, Field(max_length=...)] rather
        # than constr(...), which mypy rejects as an annotation in the modules
        # that import these models.
        "--use-annotated",
        "--target-python-version",
        TARGET_PYTHON_VERSION,
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
