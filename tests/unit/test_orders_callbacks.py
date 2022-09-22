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
from planet.cli.orders import stash_item_type, bundle_cb, Bundle

LOGGER = logging.getLogger(__name__)

TEST_ITEM_TYPE = 'psscene'


class MockContext:

    def __init__(self):
        self.obj = {}


def test_stash_item_type_success():
    ctx = MockContext()
    stash_item_type(ctx, [], TEST_ITEM_TYPE)
    assert ctx.obj == {'item_type': TEST_ITEM_TYPE}
