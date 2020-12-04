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
import logging

from planet import specs

LOGGER = logging.getLogger(__name__)

TEST_PRODUCT_BUNDLE = 'analytic'

TEST_ITEM_TYPE = 'PSOrthoTile'


def test_get_type_match():
    spec_list = [
        'Locket',
        'drop',
        'DEER']

    test_entry = 'locket'
    assert 'Locket' == specs.get_match(test_entry, spec_list)


def test_get_product_bundles():
    bundles = specs.get_product_bundles()
    assert TEST_PRODUCT_BUNDLE in bundles


def test_get_item_types():
    item_types = specs.get_item_types(TEST_PRODUCT_BUNDLE)
    assert TEST_ITEM_TYPE in item_types
