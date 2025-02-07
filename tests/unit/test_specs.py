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
import respx
import pytest

from planet import specs

LOGGER = logging.getLogger(__name__)

TEST_PRODUCT_BUNDLE = 'visual'
TEST_ITEM_TYPE = 'PSScene'
TEST_ASSET_TYPE = "basic_udm2"


def test_get_type_match():
    spec_list = ['Locket', 'drop', 'DEER']

    test_entry = 'locket'
    field_name = 'field_name'
    assert 'Locket' == specs.get_match(test_entry, spec_list, field_name)

    with pytest.raises(specs.SpecificationException):
        specs.get_match('a', ['b'], field_name)


@respx.mock
def test_validate_bundle_supported(mock_bundles):
    assert 'visual' == specs.validate_bundle(TEST_ITEM_TYPE, 'VISUAL')


@respx.mock
def test_validate_bundle_notsupported(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.validate_bundle(TEST_ITEM_TYPE, 'notsupported')


@respx.mock
def test_validate_bundle_notsupported_item_type(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.validate_item_type('wha')


@respx.mock
def test_validate_item_type_supported(mock_bundles):
    assert 'PSScene' == specs.validate_item_type('PSScene')


@respx.mock
def test_validate_item_type_notsupported_itemtype(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.validate_item_type('notsupported')


@respx.mock
def test_validate_data_item_type(mock_bundles):
    """ensure skysatvideo is included"""
    specs.validate_data_item_type('skysatvideo')


def test_validate_order_type_supported():
    assert 'full' == specs.validate_order_type('FULL')


def test_validate_order_type_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_order_type('notsupported')


def test_validate_archive_type_supported():
    assert 'zip' == specs.validate_archive_type('ZIP')


def test_validate_archive_type_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_archive_type('notsupported')


def test_validate_file_format_supported():
    assert 'COG' == specs.validate_file_format('cog')


def test_validate_file_format_notsupported():
    with pytest.raises(specs.SpecificationException):
        specs.validate_archive_type('notsupported')


@respx.mock
def test_get_product_bundles_with_item_type(mock_bundles):
    bundles = specs.get_product_bundles(item_type=TEST_ITEM_TYPE)
    assert TEST_PRODUCT_BUNDLE in bundles


@respx.mock
def test_get_product_bundles_without_item_type(mock_bundles):
    """assert an expected product bundle is in the list of all product bundles"""
    bundles = specs.get_product_bundles()
    assert TEST_PRODUCT_BUNDLE in bundles


@respx.mock
def test_get_item_types_with_bundle(mock_bundles):
    item_types = specs.get_item_types(product_bundle=TEST_PRODUCT_BUNDLE)
    assert TEST_ITEM_TYPE in item_types


@respx.mock
def test_get_item_types_without_bundle(mock_bundles):
    item_types = specs.get_item_types()
    assert TEST_ITEM_TYPE in item_types


@respx.mock
def test_validate_supported_bundles_success(mock_bundles):
    validated_bundle = specs.validate_supported_bundles(
        TEST_ITEM_TYPE,
        TEST_PRODUCT_BUNDLE,
    )
    assert validated_bundle == TEST_PRODUCT_BUNDLE


@respx.mock
def test_validate_supported_bundles_fail(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.validate_supported_bundles(
            TEST_ITEM_TYPE,
            'analytic',
        )


@respx.mock
def test_get_supported_assets_success(mock_bundles):
    supported_assets = specs.get_supported_assets(TEST_ITEM_TYPE)
    assert TEST_ASSET_TYPE in supported_assets


@respx.mock
def test_get_supported_assets_not_supported_item_type(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.get_supported_assets('notsupported')


@respx.mock
def test_validate_asset_type_supported(mock_bundles):
    """Ensures that a validated asset type for a given item type matches the
    the given asset type."""
    assert TEST_ASSET_TYPE == specs.validate_asset_type(
        TEST_ITEM_TYPE, TEST_ASSET_TYPE)


@respx.mock
def test_validate_asset_type_notsupported(mock_bundles):
    with pytest.raises(specs.SpecificationException):
        specs.validate_asset_type(TEST_ITEM_TYPE, 'notsupported')
