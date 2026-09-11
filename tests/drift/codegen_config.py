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
import pathlib

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


def codegen_argv(url: str, output: pathlib.Path) -> list:
    """Build the datamodel-codegen command line for one spec."""
    return [
        "datamodel-codegen",
        "--url",
        url,
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
