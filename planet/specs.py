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
"""Functionality for validating against the Planet API specification."""
import json
import logging
import os
from pathlib import Path


DATA_DIR = 'data'
PRODUCT_BUNDLE_SPEC_NAME = 'orders_product_bundle_2020_03_10.json'
SUPPORTED_TOOLS = ['band_math', 'clip', 'composite', 'coregister',
                   'file_format', 'reproject', 'tile', 'toar', 'harmonize']
SUPPORTED_ORDER_TYPES = ['full', 'partial']
SUPPORTED_ARCHIVE_TYPES = ['zip']

LOGGER = logging.getLogger(__name__)


class SpecificationException(Exception):
    '''No match was found'''
    pass


def validate_bundle(bundle):
    supported = get_product_bundles()
    return _validate_field(bundle, supported, 'product_bundle')


def validate_item_type(item_type, bundle, report_field_name=True):
    bundle = validate_bundle(bundle)
    supported = get_item_types(bundle)
    field_name = 'item_type' if report_field_name else None
    return _validate_field(item_type, supported, field_name)


def validate_order_type(order_type):
    return _validate_field(order_type, SUPPORTED_ORDER_TYPES, 'order_type')


def validate_archive_type(archive_type):
    return _validate_field(
        archive_type, SUPPORTED_ARCHIVE_TYPES, 'archive_type')


def validate_tool(tool):
    return _validate_field(tool, SUPPORTED_TOOLS, 'tool')


def _validate_field(value, supported, field_name=None):
    try:
        value = get_match(value, supported)
    except(NoMatchException):
        opts = ', '.join(["'"+s+"'" for s in supported])
        msg = f'\'{value}\' is not one of {opts}.'
        if field_name:
            msg = f'{field_name} - ' + msg
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
        match = next(t for t in spec_entries
                     if t.lower() == test_entry.lower())
    except(StopIteration):
        raise NoMatchException

    return match


def get_product_bundles():
    '''Get product bundles supported by Orders API.'''
    spec = _get_product_bundle_spec()
    return spec['bundles'].keys()


def get_item_types(product_bundle):
    '''Get item types supported by Orders API for the given product bundle.'''
    spec = _get_product_bundle_spec()
    return spec['bundles'][product_bundle]['assets'].keys()


def _get_product_bundle_spec_path():
    curr_path = Path(os.path.dirname(__file__))
    data_dir = curr_path.parents[0] / DATA_DIR
    return data_dir / PRODUCT_BUNDLE_SPEC_NAME


def _get_product_bundle_spec():
    with open(_get_product_bundle_spec_path()) as f:
        data = json.load(f)
    return data
