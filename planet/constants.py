# Copyright 2020 Planet Labs, Inc.
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
'''Constants used across the code base'''
import os

ENV_API_KEY = 'PL_API_KEY'
ENV_AUTH_CLIENT_CONFIG_FILE = 'PL_AUTH_CLIENT_CONFIG_FILE'
ENV_AUTH_PASSWORD = 'PL_AUTH_PASSWORD'
ENV_AUTH_PROFILE = 'PL_AUTH_PROFILE'
ENV_AUTH_SCOPES = 'PL_AUTH_SCOPES'
ENV_AUTH_TOKEN_FILE = 'PL_AUTH_TOKEN_FILE'
ENV_AUTH_USERNAME = 'PL_AUTH_USERNAME'

PLANET_BASE_URL = 'https://api.planet.com'
DEFAULT_LEGACY_PLANET_AUTH_ENDPOINT = 'https://api.planet.com/v0/auth/login'
SECRET_FILE_PATH = os.path.join(os.path.expanduser('~'), '.planet.json')
