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
import respx
from planet.cli import data
from planet.cli import orders
from planet.cli import subscriptions

LOGGER = logging.getLogger(__name__)


class MockContext:

    def __init__(self):
        self.obj = {}
        self.params = {}


@respx.mock
def test_item_types_success_data(mock_bundles):
    ctx = MockContext()
    result = data.check_item_types(ctx, 'item_types', ["PSScene"])
    assert result == ["PSScene"]


@respx.mock
def test_item_types_fail_data(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_types(ctx, 'item_types', "bad_item_type")


@respx.mock
def test_item_type_success_data(mock_bundles):
    ctx = MockContext()
    item_type = "PSScene"
    result = data.check_item_type(ctx, 'item_type', item_type)
    assert result == item_type


@respx.mock
def test_item_type_fail_data(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_type(ctx, 'item_type', "bad_item_type")


@respx.mock
def test_item_type_too_many_item_types_data(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_types(ctx, 'item_type', "PSScene,SkySatScene")


# Identical tests to above, but for subscriptions CLI
@respx.mock
def test_item_types_success_subscriptions(mock_bundles):
    ctx = MockContext()
    result = subscriptions.check_item_types(ctx, 'item_types', ["PSScene"])
    assert result == ["PSScene"]


@respx.mock
def test_item_types_fail_subscriptions(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        subscriptions.check_item_types(ctx, 'item_types', "bad_item_type")


@respx.mock
def test_item_type_too_many_item_types_subscriptions(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        subscriptions.check_item_types(ctx, 'item_type', "PSScene,SkySatScene")


@respx.mock
def test_item_type_success_orders(mock_bundles):
    ctx = MockContext()
    item_type = "PSScene"
    result = orders.check_item_type(ctx, 'item_type', item_type)
    assert result == item_type


@respx.mock
def test_item_type_fail_orders(mock_bundles):
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        orders.check_item_type(ctx, 'item_type', "bad_item_type")


@respx.mock
def test_bundle_success_orders(mock_bundles):
    ctx = MockContext()
    ctx.params = {"item_type": "PSScene"}
    bundle = "analytic_udm2"
    result = orders.check_bundle(ctx, 'bundle', bundle)
    assert result == bundle


@respx.mock
def test_bundle_fail_orders(mock_bundles):
    ctx = MockContext()
    ctx.params = {"item_type": "PSScene"}
    with pytest.raises(click.BadParameter):
        orders.check_bundle(ctx, 'bundle', "bad_bundle")
    ctx.params = {"item_type": "bad_item_type"}
    with pytest.raises(click.BadParameter):
        orders.check_bundle(ctx, 'bundle', "analytic_udm2")
