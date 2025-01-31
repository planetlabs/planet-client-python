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
import httpx
import logging
import itertools

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
HARMONIZE_TOOL_TARGET_SENSORS = ['Sentinel-2']
BAND_MATH_PIXEL_TYPE = ('Auto', '8U', '16U', '16S', '32R')
BAND_MATH_PIXEL_TYPE_DEFAULT = 'Auto'
PRODUCT_BUNDLES = None

LOGGER = logging.getLogger(__name__)


class FetchBundlesSpecError(Exception):
    """Custom exception for errors fetching the product bundles spec."""
    pass


class _LazyBundlesLoader:
    """Lazy load the product bundles spec from the API."""

    def __getitem__(self, key):
        bundles_spec_url = "https://api.planet.com/compute/ops/bundles/spec"
        retries = 2
        cache = getattr(self, "cache", None)
        if cache is None:
            for attempt in range(1, retries + 1):
                try:
                    response = httpx.get(bundles_spec_url)
                    response.raise_for_status()
                    break
                except:  # noqa: E722
                    if attempt == retries:
                        raise FetchBundlesSpecError(
                            "Unable to fetch spec from API to generate valid item types and bundles. Please retry!"
                        ) from None
            bundles = response.json()['bundles']
            item_types = set(
                itertools.chain.from_iterable(bundles[bundle]['assets'].keys()
                                              for bundle in bundles.keys()))
            cache = {
                'bundles': bundles,
                'bundle_names': bundles.keys(),
                'item_types': item_types
            }
            setattr(self, "cache", cache)
        return cache[key]


PRODUCT_BUNDLES = _LazyBundlesLoader()


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
    validate_supported_bundles(item_type, bundle)
    return _validate_field(bundle,
                           PRODUCT_BUNDLES["bundle_names"],
                           'product_bundle')


def validate_item_type(item_type):
    return _validate_field(item_type,
                           PRODUCT_BUNDLES["item_types"],
                           'item_type')


def validate_data_item_type(item_type):
    """Validate and correct capitalization of data api item type."""
    return _validate_field(item_type, get_data_item_types(), 'item_type')


def get_data_item_types():
    """Item types supported by the data api."""
    # This is a quick-fix for gh-956, to be superseded by gh-960
    return PRODUCT_BUNDLES["item_types"] | {'SkySatVideo'}


def get_bundle_names():
    """Get all product bundle names."""
    return PRODUCT_BUNDLES["bundle_names"]


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
    except FetchBundlesSpecError as e:
        raise e
    return value


def validate_supported_bundles(item_type, bundle):
    """Validate the provided item type and bundle combination are supported"""
    # get all the supported bundles for the given item type
    supported_bundles = []
    for product_bundle in PRODUCT_BUNDLES["bundle_names"]:
        available_item_types = set(
            PRODUCT_BUNDLES["bundles"][product_bundle]['assets'].keys())
        if item_type.lower() in [x.lower() for x in available_item_types]:
            supported_bundles.append(product_bundle)
    # validate the provided bundle is in the list of supported bundles
    return _validate_field(bundle, supported_bundles, 'bundle')


def validate_asset_type(item_type, asset_type):
    """Validates an asset type for a given item type."""
    # item type validation occurs inside get_supported_assets
    supported_assets = get_supported_assets(item_type)
    return _validate_field(asset_type, supported_assets, 'asset_type')


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
    if item_type:
        supported_bundles = []
        for product_bundle in PRODUCT_BUNDLES["bundle_names"]:
            available_item_types = set(
                PRODUCT_BUNDLES["bundles"][product_bundle]['assets'].keys())
            if item_type.lower() in [x.lower() for x in available_item_types]:
                supported_bundles.append(product_bundle)
        return supported_bundles

    return PRODUCT_BUNDLES["bundle_names"]


def get_item_types(product_bundle=None):
    """If given product bundle, get specific item types supported by Orders
    API. Otherwise, get all item types supported by Orders API."""
    if product_bundle:
        return set(PRODUCT_BUNDLES["bundles"][product_bundle]['assets'].keys())

    return PRODUCT_BUNDLES["item_types"]


def get_supported_assets(item_type):
    """Get all assets supported by a given item type."""
    item_type = validate_item_type(item_type)
    supported_bundles = get_product_bundles(item_type)
    supported_assets = [
        PRODUCT_BUNDLES["bundles"][bundle]["assets"][item_type]
        for bundle in supported_bundles
    ]
    supported_assets = list(set(list(itertools.chain(*supported_assets))))

    return supported_assets
