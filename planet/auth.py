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
'''Manage authentication with Planet APIs'''
from __future__ import annotations  # https://stackoverflow.com/a/33533514
import json
import logging
import os

ENV_API_KEY = 'PL_API_KEY'

SECRET_FILE_PATH = os.path.join(os.path.expanduser('~'), '.planet.json')

LOGGER = logging.getLogger(__name__)


class AuthException(Exception):
    '''exceptions thrown by Auth'''
    pass


class Auth():
    '''Handle authentication information for use with Planet APIs.'''
    def __init__(
        self,
        key: str = None,
        environment_variable: str = None,
        secret_file_path: str = None
    ):
        '''Initiaize Auth

        If key is provided, uses the key. Otherwise, tries to find key from
        environment variable. Finally, tries to find key from planet secret
        file.

        When oauth is implemented, this will attempt oauth first.

        The default environment variable is "PL_API_KEY" and the default
        secret file is named ".planet.json" and stored in the user directory.

        Parameters:
            key: API key.
            environment_variable: Alternate environment variable to read.
            secret_file_path: Alternate path to the secret file.
        '''
        self.secret_file_path = secret_file_path or SECRET_FILE_PATH
        environment_variable = environment_variable or ENV_API_KEY

        if key:
            self._auth = APIKey(key=key)
            LOGGER.info('Auth set from key parameter.')
        else:
            try:
                self._auth = APIKey.from_env(environment_variable)
                LOGGER.info('Auth set from environment variable '
                            f'{environment_variable}')
            except APIKeyException:
                try:
                    secrets = SecretFile(self.secret_file_path).read()
                    self._auth = APIKey.from_dict(secrets)
                    LOGGER.info('Auth set from secret file '
                                f'{self.secret_file_path}.')
                except FileNotFoundError:
                    raise AuthException(
                        'Could not find authentication information. Set '
                        f'environment variable {ENV_API_KEY} or store '
                        'information in secret file with Auth.store()')

    def store(self):
        try:
            secret_file = SecretFile(self.secret_file_path)
            secrets = secret_file.read()
            secrets.update(self._auth.to_dict())
        except FileNotFoundError:
            secrets = self._auth.to_dict()

        secret_file.write(secrets)

    def header(self):
        return self._auth.header()


class SecretFile():
    def __init__(self, path):
        self.path = path

    def write(
        self,
        contents: dict
    ):
        LOGGER.debug(f'Writing to {self.path}')
        with open(self.path, 'w') as fp:
            fp.write(json.dumps(contents))

    def read(self) -> dict:
        LOGGER.debug(f'Reading from {self.path}')
        with open(self.path, 'r') as fp:
            contents = json.loads(fp.read())
        return contents


class APIKeyException(Exception):
    '''exceptions thrown by APIKey'''
    pass


class APIKey():
    '''Planet API Key authentication.'''
    DICT_KEY = 'key'

    def __init__(
        self,
        key: str
    ):
        '''Initialize APIKey.

        Parameters:
            key: API key.

        Raises:
            APIKeyException: If API key is None or empty string.
        '''
        if not key:
            raise APIKeyException('API key cannot be empty.')

        self._val = key

    @classmethod
    def from_env(
        cls,
        variable_name: str
    ) -> APIKey:
        '''Get key from environment.

        Parameters:
            variable_name: Environment variable to read.
        '''
        api_key = os.getenv(variable_name)
        return cls(api_key)

    @classmethod
    def from_dict(
        cls,
        secrets: dict
    ) -> APIKey:
        '''Instantiate key from a dict.'''
        api_key = secrets.get(cls.DICT_KEY, None)
        return cls(api_key)

    def to_dict(self):
        '''Represent key as a dict.'''
        return {self.DICT_KEY: self._val}

    def header(self) -> dict:
        '''Create authorization header for api key'''
        return {'Authorization': f'api-key {self._val}'}
