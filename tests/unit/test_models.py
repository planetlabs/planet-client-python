# Copyright 2017 Planet Labs, Inc.
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
from unittest.mock import MagicMock

import pytest

from planet import models
from planet.exceptions import PagingError

LOGGER = logging.getLogger(__name__)


@pytest.mark.anyio
async def test_Paged_iterator():
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        resp = MagicMock(name='response')
        resp.json = lambda: {'_links': {}, 'items': [3, 4]}
        return resp

    paged = models.Paged(resp, get_response)
    assert [1, 2, 3, 4] == [i async for i in paged]


@pytest.mark.anyio
@pytest.mark.parametrize('limit, expected', [(0, [1, 2, 3, 4]), (1, [1])])
async def test_Paged_limit(limit, expected):
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        resp = MagicMock(name='response')
        resp.json = lambda: {'_links': {}, 'items': [3, 4]}
        return resp

    paged = models.Paged(resp, get_response, limit=limit)
    assert [i async for i in paged] == expected


@pytest.mark.anyio
async def test_Paged_break_page_cycle():
    """Check that we break out of a page cycle."""
    resp = MagicMock(name='response')
    resp.json = lambda: {'_links': {'next': 'blah'}, 'items': [1, 2]}

    async def get_response(url, method):
        return resp

    paged = models.Paged(resp, get_response, limit=None)

    with pytest.raises(PagingError):
        [item async for item in paged]
