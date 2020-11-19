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

"""Handle authentication with Planet API and management of authentication data.
"""

import json
import os

from ._fatomic import atomic_open


ENV_KEY = 'PL_API_KEY'

PLANET_AUTH_FILENAME = '.planet.json'


class APIKey(object):
    def __init__(self, value):
        self.value = value


def find_api_key():
    api_key = os.getenv(ENV_KEY)
    if api_key is None:
        contents = read_planet_auth()
        api_key = contents.get('key', None)
    return api_key


def read_planet_auth():
    fname = _planet_auth_file()
    contents = {}
    if os.path.exists(fname):
        with open(fname, 'r') as fp:
            contents = json.loads(fp.read())
    return contents


def write_planet_auth(contents):
    fname = _planet_auth_file()
    with atomic_open(fname, 'w') as fp:
        fp.write(json.dumps(contents))


def _planet_auth_file():
    return os.path.join(os.path.expanduser('~'), PLANET_AUTH_FILENAME)
