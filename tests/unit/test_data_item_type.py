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
import logging
import pytest
import click
from planet.cli.data import check_item_types

LOGGER = logging.getLogger(__name__)


class MockContext:

    def __init__(self):
        self.obj = {}


@pytest.mark.parametrize("item_type",
                         [
                             'myd09ga',
                             'sentinel1',
                             'rescene',
                             'myd09gq',
                             'psorthotile',
                             'landsat8l1g',
                             'reorthotile',
                             'sentinel2l1c',
                             'skysatscene',
                             'skysatcollect',
                             'mod09ga',
                             'psscene3band',
                             'mod09gq',
                             'psscene4band',
                             'psscene'
                         ])
def test_item_type_success(item_type):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        check_item_types(ctx, 'item_type', item_type)


def test_item_type_fail():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        check_item_types(ctx, 'item_type', "bad_item_type")
