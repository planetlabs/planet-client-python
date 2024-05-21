# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
    """Returns valid auth results as if reading a secret file"""

    def mockreturn(self):
        return {'key': 'testkey'}

    # monkeypatch fixture is not available above a function scope
    # usage: https://docs.pytest.org/en/6.2.x/reference.html#pytest.MonkeyPatch
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_SecretFile, 'read', mockreturn)
        yield


@pytest.fixture
def open_test_img():
    img_path = _test_data_path / 'test_sm.tif'
    with open(img_path, 'rb') as img:
        yield img


@pytest.fixture
def get_test_file_json():

    def func(filename):
        file_path = _test_data_path / filename
        with open(file_path, 'r') as f:
            res = json.load(f)
        return res

    return func


@pytest.fixture
def search_result(get_test_file_json):
    filename = 'search_result_20200130_093253_ssc6_u0001.json'
    return get_test_file_json(filename)


@pytest.fixture
def order_description(get_test_file_json):
    filename = 'order_description_b0cb3448-0a74-11eb-92a1-a3d779bb08e0.json'
    return get_test_file_json(filename)


@pytest.fixture
def order_request(get_test_file_json):
    filename = 'order_details_psorthotile_analytic.json'
    return get_test_file_json(filename)


@pytest.fixture
def orders_page(get_test_file_json):
    filename = 'orders_page.json'
    return get_test_file_json(filename)


@pytest.fixture
def oid():
    return 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'


@pytest.fixture
def search_id():
    return '20200130_093253_ssc6_u0001'


@pytest.fixture
def write_to_tmp_json_file(tmp_path):

    def write(data, filename):
        cc = tmp_path / filename
        with open(cc, 'w') as fp:
            json.dump(data, fp)
        return cc

    return write


@pytest.fixture
def geom_geojson():
    # these need to be tuples, not list, or they will be changed
    # by shapely
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [37.791595458984375, 14.84923123791421],
                [37.90214538574219, 14.84923123791421],
                [37.90214538574219, 14.945448293647944],
                [37.791595458984375, 14.945448293647944],
                [37.791595458984375, 14.84923123791421],
            ]
        ],
    }  # yapf: disable


@pytest.fixture
def str_geom_reference():
    return "pl:features/my/water-fields-RqB0NZ5/rmQEGqm"


@pytest.fixture
def geom_reference():
    return {
        "type": "ref",
        "content": "pl:features/my/water-fields-RqB0NZ5/rmQEGqm",
    }  # yapf: disable


@pytest.fixture
def feature_geojson(geom_geojson):
    return {"type": "Feature", "properties": {}, "geometry": geom_geojson}


@pytest.fixture
def featurecollection_geojson(feature_geojson):
    return {"type": "FeatureCollection", "features": [feature_geojson]}


@pytest.fixture
def point_geom_geojson():
    return {
        "type": "Point",
        "coordinates": [37.791595458984375, 14.84923123791421]
    }


@pytest.fixture
def multipolygon_geom_geojson():
    return {
        "type":
        "MultiPolygon",
        "coordinates":
        [[[[37.791595458984375, 14.84923123791421],
          [37.90214538574219, 14.84923123791421],
          [37.90214538574219, 14.945448293647944],
          [37.791595458984375, 14.945448293647944],
          [37.791595458984375, 14.84923123791421]]]]
    }  # yapf: disable


@pytest.fixture
def anyio_backend():
    return 'asyncio'
