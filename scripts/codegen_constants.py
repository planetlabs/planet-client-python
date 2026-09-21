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
"""Constants for Pydantic model code generation.

Separated from the codegen logic so the spec URLs and output paths can be
read and changed without reading the generator. Adding an API means adding
one line to SPECS.
"""
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent

# Where generated models are written. One module per entry in SPECS.
MODELS_DIR = REPO_ROOT / "planet" / "types"

# Live OpenAPI specs, keyed by the module name they generate.
# TODO: extend to other APIs as Pydantic models are adopted:
#   "subscriptions": "https://api.planet.com/subscriptions/v1/spec",
#   "orders":        "https://api.planet.com/compute/ops/spec",
#   "data":          "https://api.planet.com/data/v1/spec",
SPECS = {
    "destinations": "https://api.planet.com/destinations/v1/spec",
}

# Prepended to every generated module.
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
DROP_CONSTRAINT_ANY_OF: set[str] = {
    "DestinationPatchRequest",
}

# datamodel-codegen target. Pinned, not inferred from the interpreter running
# codegen: output differs between Python versions, which would fail the drift
# check. 3.10 is the project's requires-python floor.
TARGET_PYTHON_VERSION = "3.10"
