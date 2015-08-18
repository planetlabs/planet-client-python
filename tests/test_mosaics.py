# Copyright 2015 Planet Labs, Inc.
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
from _common import read_fixture
import json
import os
from planet import api
from requests_mock import Mocker


client = api.Client(api_key='xyz')


def test_list_mosaics():

    with Mocker() as m:

        text = read_fixture('list-mosaics.json')
        uri = os.path.join(client.base_url, 'mosaics/')
        m.get(uri, text=text, status_code=200)

        r = client.list_mosaics()

        assert r.response.status_code == 200
        assert r.get() == json.loads(text)


def test_get_mosaic():

    mosaic_name = 'color_balance_mosaic'

    with Mocker() as m:

        text = read_fixture('get-mosaic.json')
        uri = os.path.join(client.base_url,
                           'mosaics/%s/' % mosaic_name)
        m.get(uri, text=text, status_code=200)

        r = client.get_mosaic(mosaic_name)

        assert r.response.status_code == 200
        assert r.get() == json.loads(text)


def test_get_mosaic_quads():

    mosaic_name = 'color_balance_mosaic'

    with Mocker() as m:

        text = read_fixture('get-mosaic-quads.json')
        uri = os.path.join(client.base_url,
                           'mosaics/%s/quads/?count=50' % mosaic_name)

        m.get(uri, text=text, status_code=200)

        r = client.get_mosaic_quads(mosaic_name, count=50)

        assert r.response.status_code == 200
        assert r.get() == json.loads(text)
