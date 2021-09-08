# Copyright 2020 Planet Labs, Inc.
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

from tqdm.asyncio import tqdm

LOGGER = logging.getLogger(__name__)


class ProgressBar():
    def __init__(self):
        self.bar = None

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
        order_id: str = None,
        state: str = None
    ):
        """Initialize the object.

        Parameters:
            filename: Name of file to display.
            size: File size in bytes.
            unit: Value to scale number of report iterations.
                (e.g. 1024*1024 scales to reporting in Megabytes.)
        """

        self.state = state or ''
        self.order_id = order_id or ''
        super().__init__()

    def open_bar(self):
        """Initialize and start the progress bar."""
        self.bar = tqdm(
            bar_format="{elapsed} - {desc} - {postfix[0]}: {postfix[1]}",
            desc=self.desc, postfix=["state", self.state])

    @property
    def desc(self):
        return f'order {self.order_id}'

    def update(self, state=None, order_id=None):
        if state:
            if state != self.state:
                LOGGER.info('{order_id} state: {state}')
            self.state = state
            self.bar.postfix[1] = self.state

        if order_id:
            self.order_id = order_id
            self.bar.set_description_str(self.desc, refresh=False)

        self.bar.refresh()

        LOGGER.debug(str(self.bar))


class FileDownloadBar(ProgressBar):
    """Bar reporter of file download progress.

    Example:
        ```python
        from planet import reporting

        with reporting.FileDownloadBar('img.tif', 100000) as bar:
            bar.update(1000)
            ...
        ```
    """
    def __init__(
        self,
        filename: str,
        size: int,
        unit: int = None,
        disable: bool = False
    ):
        """Initialize the object.

        Parameters:
            filename: Name of file to display.
            size: File size in bytes.
            unit: Value to scale number of report iterations.
                (e.g. 1024*1024 scales to reporting in Megabytes.)
        """
        self.filename = filename
        self.size = size
        self.unit = unit or 1024*1024
        super().__init__()

    def open_bar(self):
        """Initialize and start the progress bar."""
        self.bar = tqdm(
            total=self.size,
            unit_scale=True,
            unit_divisor=self.unit,
            unit='B',
            desc=self.filename,
            disable=self.disable)

    def update(self, downloaded_amt, logger=None):
        self.bar.update(downloaded_amt)
        LOGGER.debug(str(self.bar))
