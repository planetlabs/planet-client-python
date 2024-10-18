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
"""Functionality for validating against the Planet API specification."""
import json
import logging
import itertools
from .constants import DATA_DIR

PRODUCT_BUNDLE_SPEC_NAME = 'orders_product_bundle_2024-08-12.json'
SUPPORTED_TOOLS = [
    'bandmath',
    'clip',
    'composite',
    'coregister',
    'file_format',
    'reproject',
    'tile',
    'toar',
    'harmonize'
]
SUPPORTED_ORDER_TYPES = ['full', 'partial']
SUPPORTED_ARCHIVE_TYPES = ['zip']
SUPPORTED_FILE_FORMATS = ['COG', 'PL_NITF']
HARMONIZE_TOOL_TARGET_SENSORS = ('Sentinel-2', 'PS2')
BAND_MATH_PIXEL_TYPE = ('Auto', '8U', '16U', '16S', '32R')
BAND_MATH_PIXEL_TYPE_DEFAULT = 'Auto'

LOGGER = logging.getLogger(__name__)


class NoMatchException(Exception):
    """No match was found"""
    pass


class SpecificationException(Exception):
    """No match was found"""

    def __init__(self, value, supported, field_name):
        self.value = value
        self.supported = supported
        self.field_name = field_name
        self.opts = ', '.join(["'" + s + "'" for s in supported])

    def __str__(self):
        return (f'{self.field_name} - \'{self.value}\' is not one of '
                f'{self.opts}.')


def validate_bundle(item_type, bundle):
    all_product_bundles = get_product_bundles()
    validate_supported_bundles(item_type, bundle, all_product_bundles)
    return _validate_field(bundle, all_product_bundles, 'product_bundle')


def validate_item_type(item_type):
    supported_item_types = get_item_types()
    return _validate_field(item_type, supported_item_types, 'item_type')


def validate_data_item_type(item_type):
    """Validate and correct capitalization of data api item type."""
    return _validate_field(item_type, get_data_item_types(), 'item_type')


def get_data_item_types():
    """Item types supported by the data api."""
    # This is a quick-fix for gh-956, to be superseded by gh-960
    return get_item_types() | {'SkySatVideo'}


def validate_order_type(order_type):
    return _validate_field(order_type, SUPPORTED_ORDER_TYPES, 'order_type')


def validate_archive_type(archive_type):
    return _validate_field(archive_type,
                           SUPPORTED_ARCHIVE_TYPES,
                           'archive_type')


def validate_tool(tool):
    return _validate_field(tool, SUPPORTED_TOOLS, 'tool')


def validate_file_format(file_format):
    return _validate_field(file_format, SUPPORTED_FILE_FORMATS, 'file_format')


def _validate_field(value, supported, field_name):
    try:
        value = get_match(value, supported, field_name)
    except (NoMatchException):
        raise SpecificationException(value, supported, field_name)
    return value


def validate_supported_bundles(item_type, bundle, all_product_bundles):
    spec = _get_product_bundle_spec()

    supported_bundles = []
    for product_bundle in all_product_bundles:
        availible_item_types = set(
            spec['bundles'][product_bundle]['assets'].keys())
        if item_type.lower() in [x.lower() for x in availible_item_types]:
            supported_bundles.append(product_bundle)

    return _validate_field(bundle, supported_bundles, 'bundle')


def validate_asset_type(item_type, asset_type):
    """Validates an asset type for a given item type."""
    item_type = validate_item_type(item_type)
    supported_assets = get_supported_assets(item_type)

    return _validate_field(asset_type, supported_assets, 'asset_type')


def _get_product_bundle_spec():
    with open(DATA_DIR / PRODUCT_BUNDLE_SPEC_NAME) as f:
        data = json.load(f)
    return data


def get_match(test_entry, spec_entries, field_name):
    """Find and return matching spec entry regardless of capitalization.

    This is helpful for working with the API spec, where the capitalization
    is hard to remember but must be exact otherwise the API throws an
    exception."""
    try:
        match = next(e for e in spec_entries
                     if e.lower() == test_entry.lower())
    except (StopIteration):
        raise SpecificationException(test_entry, spec_entries, field_name)

    return match


def get_product_bundles(item_type=None):
    """Get product bundles supported by Orders API."""
    spec = _get_product_bundle_spec()

    if item_type:
        all_product_bundles = get_product_bundles()

        supported_bundles = []
        for product_bundle in all_product_bundles:
            availible_item_types = set(
                spec['bundles'][product_bundle]['assets'].keys())
            if item_type.lower() in [x.lower() for x in availible_item_types]:
                supported_bundles.append(product_bundle)
    else:
        supported_bundles = spec['bundles'].keys()
    return supported_bundles


def get_item_types(product_bundle=None):
    """If given product bundle, get specific item types supported by Orders
    API. Otherwise, get all item types supported by Orders API."""
    spec = _get_product_bundle_spec()

    if product_bundle:
        item_types = set(spec['bundles'][product_bundle]['assets'].keys())
    else:
        item_types = set(
            itertools.chain.from_iterable(
                spec['bundles'][bundle]['assets'].keys()
                for bundle in get_product_bundles()))

    return item_types


def get_supported_assets(item_type):
    """Get all assets supported by a given item type."""
    item_type = validate_item_type(item_type)
    supported_bundles = get_product_bundles(item_type)
    spec = _get_product_bundle_spec()
    supported_assets = [
        spec['bundles'][bundle]["assets"][item_type]
        for bundle in supported_bundles
    ]
    supported_assets = list(set(list(itertools.chain(*supported_assets))))

    return supported_assets
