# Copyright 2020 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import os
from pathlib import Path

import pytest

from planet.auth import _SecretFile

_here = Path(os.path.abspath(os.path.dirname(__file__)))
_test_data_path = _here / 'data'


@pytest.fixture(autouse=True, scope='module')
def test_secretfile_read():
    '''Returns valid auth results as if reading a secret file'''
    def mockreturn(self):
        return {'key': 'testkey'}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_SecretFile, 'read', mockreturn)
        yield


@pytest.fixture
def open_test_img():
    img_path = _test_data_path / 'test_sm.tif'
    with open(img_path, 'rb') as img:
        yield img


def _get_file_json(filename):
    file_path = _test_data_path / filename
    return json.load(open(file_path, 'r'))


@pytest.fixture
def order_description():
    filename = 'order_description_b0cb3448-0a74-11eb-92a1-a3d779bb08e0.json'
    return _get_file_json(filename)


@pytest.fixture
def order_details():
    filename = 'order_details_psorthotile_analytic.json'
    return _get_file_json(filename)


@pytest.fixture
def orders_page():
    filename = 'orders_page.json'
    return _get_file_json(filename)


@pytest.fixture
def oid():
    return 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'
