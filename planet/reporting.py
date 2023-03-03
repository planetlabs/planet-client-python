# Copyright 2021 Planet Labs, Inc.
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
"""Functionality for reporting progress."""
import logging
from typing import Optional

from tqdm.asyncio import tqdm

LOGGER = logging.getLogger(__name__)


class ProgressBar:
    """Abstract base class for progress bar reporters."""

    def __init__(self, disable: bool = False):
        self.bar = None
        self.disable = disable

    def __str__(self):
        return str(self.bar)

    def __enter__(self):
        self.open_bar()
        return self

    def __exit__(self, *args):
        self.bar.close()

    def open_bar(self):
        """Initialize and start the progress bar."""
        return NotImplementedError


class StateBar(ProgressBar):
    """Bar reporter of order state.

    Example:
        ```python
        from planet import reporting

        with reporting.StateBar(state='creating') as bar:
            bar.update(state='created', order_id='oid')
            ...
        ```
    """

    def __init__(
        self,
        order_id: Optional[str] = None,
        state: Optional[str] = None,
        disable: bool = False,
    ):
        """Initialize the object.

        Parameters:
            order_id: Id of the order.
            state: State of the order.
        """

        self.state = state or ''
        self.order_id = order_id or ''
        super().__init__(disable=disable)

    def open_bar(self):
        """Initialize and start the progress bar."""
        self.bar = tqdm(
            bar_format="{elapsed} - {desc} - {postfix[0]}: {postfix[1]}",
            desc=self.desc,
            postfix=["state", self.state],
            disable=self.disable)

    @property
    def desc(self):
        return f'order {self.order_id}'

    def update_state(self, state: str):
        """Simple function to be used as a callback for state reporting"""
        self.update(state=state)

    def update(self,
               state: Optional[str] = None,
               order_id: Optional[str] = None):
        if state:
            self.state = state
            if self.bar is not None:
                try:
                    self.bar.postfix[1] = self.state
                except AttributeError:
                    # If the bar is disabled, attempting to access
                    # self.bar.postfix will result in an error. In this
                    # case, just skip it.
                    pass

        if order_id:
            self.order_id = order_id
            if self.bar is not None:
                self.bar.set_description_str(self.desc, refresh=False)

        if self.bar is not None:
            self.bar.refresh()


class AssetStatusBar(ProgressBar):
    """Bar reporter of asset status."""

    def __init__(
        self,
        item_type,
        item_id,
        asset_type,
        disable: bool = False,
    ):
        """Initialize the object.
        """
        self.item_type = item_type
        self.item_id = item_id
        self.asset_type = asset_type
        self.status = ''
        super().__init__(disable=disable)

    def open_bar(self):
        """Initialize and start the progress bar."""
        self.bar = tqdm(
            bar_format="{elapsed} - {desc} - {postfix[0]}: {postfix[1]}",
            desc=self.desc,
            postfix=["status", self.status],
            disable=self.disable)

    @property
    def desc(self):
        return f'{self.item_type} {self.item_id} {self.asset_type}'

    def update(self, status: str):
        self.status = status

        if self.bar is not None:
            try:
                self.bar.postfix[1] = self.status
            except AttributeError:
                # If the bar is disabled, attempting to access self.bar.postfix
                # will result in an error. In this case, just skip it.
                pass

        if self.bar is not None:
            self.bar.refresh()
