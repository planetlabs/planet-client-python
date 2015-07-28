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
import os
import json
import unittest
from requests_mock import Mocker
from planet import api


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIR = os.path.join(TEST_DIR, 'fixtures')


class TestMosaics(unittest.TestCase):

    def setUp(self):
        self.client = api.Client(api_key='xyz')


    def test_list_mosaics(self):

        fixture_path = os.path.join(FIXTURE_DIR, 'list-mosaics.json')
        with Mocker() as m, open(fixture_path) as f:

            text = f.read()
            uri = os.path.join(self.client.base_url, 'mosaics')
            m.get(uri, text=text, status_code=200)

            r = self.client.list_mosaics()

            assert r.response.status_code == 200
            assert r.get() == json.loads(text)


    def test_get_mosaic(self):

        mosaic_name = 'color_balance_mosaic'

        fixture_path = os.path.join(FIXTURE_DIR, 'get-mosaic.json')
        with Mocker() as m, open(fixture_path) as f:

            text = f.read()
            uri = os.path.join(self.client.base_url,
                               'mosaics/%s' % mosaic_name)
            m.get(uri, text=text, status_code=200)

            r = self.client.get_mosaic(mosaic_name)

            assert r.response.status_code == 200
            assert r.get() == json.loads(text)


    def test_get_mosaic_quads(self):
        
        mosaic_name = 'color_balance_mosaic'
        
        fixture_path = os.path.join(FIXTURE_DIR, 'get-mosaic-quads.json')
        with Mocker() as m, open(fixture_path) as f:
            
            text = f.read()
            uri = os.path.join(self.client.base_url, 'mosaics/%s/quads' % mosaic_name)
            
            m.get(uri, text=text, status_code=200)
            
            r = self.client.get_mosaic_quads(mosaic_name, intersect='', count=50)
            
            assert r.response.status_code == 200
            assert r.get() == json.loads(text)

