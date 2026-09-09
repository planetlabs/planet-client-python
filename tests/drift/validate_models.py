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
"""Pre-release drift detection: regenerate Pydantic models and diff against committed files.

How it works:
  - datamodel-codegen fetches the live OpenAPI spec and generates models into a temp file.
  - The output is compared against the committed file in planet/api_models/.
  - The test fails if they differ, indicating the spec has changed.

When a test fails:
  1. Review what changed in the spec.
  2. Regenerate the committed models:
       nox -s generate_models
  3. Update the client code if the API change requires it.
  4. Commit the updated models.
"""
import pathlib
import subprocess
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
MODELS_DIR = REPO_ROOT / "planet" / "api_models"

HEADER = ("# flake8: noqa\n"
          "# fmt: off\n"
          "# Generated code — do not edit manually.\n"
          "# To regenerate, run:\n"
          "#   nox -s generate_models\n"
          "# Requires: uv tool install 'datamodel-code-generator[http]'")

SPECS = {
    "destinations": "https://api.planet.com/destinations/v1/spec",
}


def _regenerate(url: str, output: pathlib.Path) -> None:
    result = subprocess.run(
        [
            "datamodel-codegen",
            "--url",
            url,
            "--input-file-type",
            "openapi",
            "--output",
            str(output),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--custom-file-header",
            HEADER,
            "--formatters",
            "builtin",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"datamodel-codegen failed:\n{result.stderr}")


@pytest.mark.parametrize("name,url", SPECS.items())
def test_models_match_spec(name, url):
    committed = MODELS_DIR / f"{name}.py"

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)

    try:
        _regenerate(url, tmp_path)

        generated = tmp_path.read_text()
        current = committed.read_text()

        if generated != current:
            pytest.fail(
                f"planet/api_models/{name}.py is out of date with the live spec.\n"
                f"Run `nox -s generate_models` to regenerate, then commit the result."
            )
    finally:
        tmp_path.unlink(missing_ok=True)
