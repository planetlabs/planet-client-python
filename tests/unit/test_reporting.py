# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
import logging
import re

from planet import reporting

LOGGER = logging.getLogger(__name__)


def test_StateBar___init___default():
    with reporting.StateBar() as bar:
        expected_init = '..:.. - order  - state: '
        assert (re.fullmatch(expected_init, str(bar)))

        expected_update = '..:.. - order 1 - state: init'
        bar.update(order_id='1', state='init')
        assert (re.fullmatch(expected_update, str(bar)))


def test_StateBar___init___stateandorder():
    with reporting.StateBar(order_id='1', state='init') as bar:
        expected_init = '..:.. - order 1 - state: init'
        assert (re.fullmatch(expected_init, str(bar)))


def test_StateBar___init___disabled():
    """Make sure it doesn't error out when disabled"""
    with reporting.StateBar(disable=True) as bar:
        assert bar.bar.disable

        # just make sure this doesn't error out
        bar.update(order_id='1', state='init')


def test_StateBar_update():
    with reporting.StateBar() as bar:
        expected_update = '..:.. - order 1 - state: init'
        bar.update(order_id='1', state='init')
        assert (re.fullmatch(expected_update, str(bar)))


def test_StateBar_update_state():
    with reporting.StateBar() as bar:
        expected_update = '..:.. - order  - state: init'
        bar.update_state('init')
        assert (re.fullmatch(expected_update, str(bar)))


def test_AssetStatusBar_disabled():
    """Make sure it doesn't error out when disabled"""
    with reporting.AssetStatusBar('item-type',
                                  'item_id',
                                  'asset_type',
                                  disable=True) as bar:
        assert bar.bar.disable

        # just make sure this doesn't error out
        bar.update(status='init')


def test_AssetStatusBar_update():
    """Status is changed with update"""
    with reporting.AssetStatusBar('item-type', 'item_id', 'asset_type') as bar:
        assert ('status: init') not in str(bar)

        bar.update(status='init')
        assert ('status: init') in str(bar)
