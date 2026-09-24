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
"""Typed request and response models, generated from Planet's OpenAPI specs.

Requires pydantic, which is an optional dependency:

    pip install planet[models]

The rest of the SDK does not import this package. Clients return plain dicts;
these models are opt-in validation on top of them:

    from planet.types.destinations import Destination

    dest = Destination.model_validate(client.get_destination(dest_id))

To regenerate after a spec change, run `nox -s generate_models`.
"""
try:
    import pydantic as _pydantic  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "planet.types requires pydantic, which is not installed. "
        "Install it with: pip install planet[models]") from exc
