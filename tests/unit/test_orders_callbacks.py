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
from planet.cli.orders import stash_item_type, bundle_cb
from planet.specs import get_product_bundles

LOGGER = logging.getLogger(__name__)

TEST_ITEM_TYPE = 'psscene'
ALL_PRODUCT_BUNDLES = [
    'analytic',
    'analytic_udm2',
    'analytic_3b_udm2',
    'analytic_5b',
    'analytic_5b_udm2',
    'analytic_8b_udm2',
    'visual',
    'uncalibrated_dn',
    'uncalibrated_dn_udm2',
    'basic_analytic',
    'basic_analytic_udm2',
    'basic_analytic_8b_udm2',
    'basic_uncalibrated_dn',
    'basic_uncalibrated_dn_udm2',
    'analytic_sr',
    'analytic_sr_udm2',
    'analytic_8b_sr_udm2',
    'basic_uncalibrated_dn_nitf',
    'basic_uncalibrated_dn_nitf_udm2',
    'basic_analytic_nitf',
    'basic_analytic_nitf_udm2',
    'basic_panchromatic',
    'basic_panchromatic_dn',
    'panchromatic',
    'panchromatic_dn',
    'panchromatic_dn_udm2',
    'pansharpened',
    'pansharpened_udm2',
    'basic_l1a_dn'
]


class MockContext:

    def __init__(self):
        self.obj = {}


class Param(object):

    def __init__(self):
        self.name = 'bundle'


def test_stash_item_type_success():
    ctx = MockContext()
    stash_item_type(ctx, 'item_type', TEST_ITEM_TYPE)
    assert ctx.obj['item_type'] == TEST_ITEM_TYPE


def test_bundle_cb_pass_through():
    """Do nothing if the bundle value is defined."""
    ctx = MockContext()
    ctx.obj['item_type'] = TEST_ITEM_TYPE
    assert bundle_cb(ctx, 'bundle', 'anything')


def test_bundle_cb_missing_parameter():
    """If bundle option is missing, print helpful error using item type information."""
    ctx = MockContext()
    ctx.obj['item_type'] = TEST_ITEM_TYPE
    param = Param()

    all_bundles = get_product_bundles()
    all_bundles_formatted = [bundle + "\n\t" for bundle in all_bundles]
    msg = f"Missing option '--bundle'. Choose from:\n{all_bundles_formatted}."

    with pytest.raises(click.ClickException, match=msg):
        bundle_cb(ctx, param, None)
