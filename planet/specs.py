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

LOGGER = logging.getLogger(__name__)


def get_match(test_entry, spec_entries):
    '''Find and return matching spec entry regardless of capitalization.

    This is helpful for working with the API spec, where the capitalization
    is hard to remember but must be exact otherwise the API throws an
    exception.'''
    return next(t for t in spec_entries
                if t.lower() == test_entry.lower())


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
