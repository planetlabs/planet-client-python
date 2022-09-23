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
import logging
import pytest
from planet.specs import SpecificationException
from planet.cli.data import check_item_types

LOGGER = logging.getLogger(__name__)


class MockContext:

    def __init__(self):
        self.obj = {}


@pytest.mark.parametrize("item_types",
                         [
                             'PSScene3Band',
                             'MOD09GQ',
                             'MYD09GA',
                             'REOrthoTile',
                             'SkySatCollect',
                             'SkySatScene',
                             'MYD09GQ',
                             'Landsat8L1G',
                             'Sentinel2L1C',
                             'MOD09GA',
                             'Sentinel1',
                             'PSScene',
                             'PSOrthoTile',
                             'PSScene4Band',
                             'REScene'
                         ])
def test_item_type_success(item_types):
    ctx = MockContext()
    result = check_item_types(ctx, 'item_types', [item_types])
    assert result == [item_types]


def test_item_type_fail():
    ctx = MockContext()
    with pytest.raises(SpecificationException):
        check_item_types(ctx, 'item_type', "bad_item_type")
