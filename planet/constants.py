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
"""Constants used across the code base"""
import os
from pathlib import Path

# NOTE: entries are given in alphabetical order

DATA_DIR = Path(os.path.dirname(__file__)) / 'data'

ENV_API_KEY = 'PL_API_KEY'

PLANET_BASE_URL = 'https://api.planet.com'

SECRET_FILE_PATH = Path(os.path.expanduser('~')) / '.planet.json'
