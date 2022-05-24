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
import copy

import pytest

from planet import Session


@pytest.fixture
@pytest.mark.asyncio
async def session():
    async with Session() as ps:
        yield ps


@pytest.fixture
def order_descriptions(order_description):
    order1 = order_description
    order1['id'] = 'oid1'
    order2 = copy.deepcopy(order_description)
    order2['id'] = 'oid2'
    order3 = copy.deepcopy(order_description)
    order3['id'] = 'oid3'
    return [order1, order2, order3]
