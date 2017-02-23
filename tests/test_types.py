# Copyright 2017 Planet Labs, Inc.
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
# limitations under the License

from planet.scripts.types import _allowed_item_types
from planet.scripts.types import AssetType
from planet.scripts.types import ItemType
import pytest


def test_item_type():
    t = ItemType()
    assert t.convert('all', None, None) == _allowed_item_types
    assert set(t.convert('psscene', None, None)) == \
        set(['PSScene3Band', 'PSScene4Band'])
    assert t.convert('Sentinel2L1C', None, None) == ['Sentinel2L1C']

    with pytest.raises(Exception) as e:
        t.convert('x', None, None)
    assert 'invalid choice: x' in str(e.value)


def test_asset_type():
    t = AssetType()
    assert set(t.convert('visual*', None, None)) == \
        set(['visual', 'visual_xml'])
    assert set(t.convert('*data_*', None, None)) == \
        set(['metadata_aux', 'metadata_txt'])
    assert t.convert('analytic', None, None) == ['analytic']

    with pytest.raises(Exception) as e:
        t.convert('x', None, None)
    assert 'invalid choice: x' in str(e.value)
