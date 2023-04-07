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
from planet.cli import data
from planet.cli import subscriptions

LOGGER = logging.getLogger(__name__)


class MockContext:

    def __init__(self):
        self.obj = {}


def test_item_types_success_data():
    ctx = MockContext()
    result = data.check_item_types(ctx, 'item_types', ["PSScene"])
    assert result == ["PSScene"]


def test_item_types_fail_data():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_types(ctx, 'item_types', "bad_item_type")


def test_item_type_success_data():
    ctx = MockContext()
    item_type = "PSScene"
    result = data.check_item_type(ctx, 'item_type', item_type)
    assert result == item_type


def test_item_type_fail_data():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_type(ctx, 'item_type', "bad_item_type")


def test_item_type_too_many_item_types_data():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        data.check_item_types(ctx, 'item_type', "PSScene,SkySatScene")


# Identical tests to above, but for subscriptions CLI
def test_item_types_success_subscriptions():
    ctx = MockContext()
    result = subscriptions.check_item_types(ctx, 'item_types', ["PSScene"])
    assert result == ["PSScene"]


def test_item_types_fail_subscriptions():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        subscriptions.check_item_types(ctx, 'item_types', "bad_item_type")


def test_item_type_success_subscriptions():
    ctx = MockContext()
    item_type = "PSScene"
    result = subscriptions.check_item_type(ctx, 'item_type', item_type)
    assert result == item_type


def test_item_type_fail_subscriptions():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        subscriptions.check_item_type(ctx, 'item_type', "bad_item_type")


def test_item_type_too_many_item_types_subscriptions():
    ctx = MockContext()
    with pytest.raises(click.BadParameter):
        subscriptions.check_item_types(ctx, 'item_type', "PSScene,SkySatScene")
