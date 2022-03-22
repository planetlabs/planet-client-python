# Copyright 2020 Planet Labs, PBC.
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

from planet import specs

LOGGER = logging.getLogger(__name__)

TEST_PRODUCT_BUNDLE = 'visual'
# must be a valid item type for TEST_PRODUCT_BUNDLE
TEST_ITEM_TYPE = 'PSScene'


def test_get_type_match():
    spec_list = ['Locket', 'drop', 'DEER']

    test_entry = 'locket'
    assert 'Locket' == specs.get_match(test_entry, spec_list)

    with pytest.raises(specs.NoMatchException):
        specs.get_match('a', ['b'])


def test_validate_bundle_supported():
    assert 'analytic' == specs.validate_bundle('ANALYTIC')


def test_validate_bundle_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_bundle('notsupported')


def test_validate_item_type_supported():
    assert 'PSOrthoTile' == specs.validate_item_type('psorthotile', 'analytic')


def test_validate_item_type_notsupported_bundle():
    with pytest.raises(specs.SpecificationException):
        specs.validate_item_type('psorthotile', 'wha')


def test_validate_item_type_notsupported_itemtype():
    with pytest.raises(specs.SpecificationException):
        specs.validate_item_type('notsupported', 'analytic')


def test_validate_order_type_supported():
    assert 'full' == specs.validate_order_type('FULL')


def test_validate_order_type_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_order_type('notsupported')


def test_validate_arhive_type_supported():
    assert 'zip' == specs.validate_archive_type('ZIP')


def test_validate_arhive_type_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_archive_type('notsupported')


def test_validate_file_format_supported():
    assert 'COG' == specs.validate_file_format('cog')


def test_validate_file_format_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_archive_type('notsupported')


def test_get_product_bundles():
    bundles = specs.get_product_bundles()
    assert TEST_PRODUCT_BUNDLE in bundles


def test_get_item_types():
    item_types = specs.get_item_types(TEST_PRODUCT_BUNDLE)
    assert TEST_ITEM_TYPE in item_types
