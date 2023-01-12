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
"""Example or more like proof of concept for a simple synchronous way to search
with the data api.
"""
from planet import data_filter
from planet.clients import data

# do we get as many results as expected?
print(
    len([
        r for r in data.search(
            ['PSScene'], data_filter.and_filter([]), limit=500)
    ]))

# what if we just want the first item?
print(next(data.search(['PSScene'], data_filter.and_filter([]), limit=500)))
