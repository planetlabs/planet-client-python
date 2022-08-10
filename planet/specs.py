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

from .constants import DATA_DIR

PRODUCT_BUNDLE_SPEC_NAME = 'orders_product_bundle_2022_02_02.json'
SUPPORTED_TOOLS = [
    'band_math',
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

LOGGER = logging.getLogger(__name__)


class SpecificationException(Exception):
    '''No match was found'''
    pass


def validate_bundle(bundle):
    supported = get_product_bundles()
    return _validate_field(bundle, supported, 'product_bundle')


def validate_item_type(item_type, bundle):
    bundle = validate_bundle(bundle)
    supported = get_item_types(bundle)
    return _validate_field(item_type, supported, 'item_type')


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
        value = get_match(value, supported)
    except (NoMatchException):
        opts = ', '.join(["'" + s + "'" for s in supported])
        msg = f'{field_name} - \'{value}\' is not one of {opts}.'
        raise SpecificationException(msg)
    return value


class NoMatchException(Exception):
    '''No match was found'''
    pass


def get_match(test_entry, spec_entries):
    '''Find and return matching spec entry regardless of capitalization.

    This is helpful for working with the API spec, where the capitalization
    is hard to remember but must be exact otherwise the API throws an
    exception.'''
    try:
        match = next(e for e in spec_entries
                     if e.lower() == test_entry.lower())
    except (StopIteration):
        raise NoMatchException('{test_entry} should be one of {spec_entries}')

    return match


def get_product_bundles():
    '''Get product bundles supported by Orders API.'''
    spec = _get_product_bundle_spec()
    return spec['bundles'].keys()


def get_item_types(product_bundle=None):
    '''If given product bundle, get specific item types supported by Orders
    API. Otherwise, get all item types supported by Orders API.'''
    spec = _get_product_bundle_spec()
    if product_bundle:
        item_types = spec['bundles'][product_bundle]['assets'].keys()
    else:
        product_bundle = get_product_bundles()
        all_item_types = []
        for bundle in product_bundle:
            all_item_types += [*spec['bundles'][bundle]['assets'].keys()]
        item_types = set(all_item_types)
    return item_types


def _get_product_bundle_spec():
    with open(DATA_DIR / PRODUCT_BUNDLE_SPEC_NAME) as f:
        data = json.load(f)
    return data
