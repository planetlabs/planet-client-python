# Copyright 2015 Planet Labs, Inc.
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

import os
from .utils import read_planet_json

ENV_KEY = 'PL_API_KEY'


class APIKey(object):
    def __init__(self, value):
        self.value = value


def find_api_key():
    api_key = os.getenv(ENV_KEY)
    if api_key is None:
        contents = read_planet_json()
        api_key = contents.get('key', None)
    return api_key
