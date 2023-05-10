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
'''Manage authentication with Planet APIs'''
from __future__ import annotations  # https://stackoverflow.com/a/33533514
import abc
import json
import logging
import os
import pathlib
import stat
import typing
from typing import Optional

import httpx
import jwt

from . import http
from .constants import ENV_API_KEY, PLANET_BASE_URL, SECRET_FILE_PATH
from .exceptions import AuthException

LOGGER = logging.getLogger(__name__)

BASE_URL = f'{PLANET_BASE_URL}/v0/auth'

AuthType = httpx.Auth


class Auth(metaclass=abc.ABCMeta):
    '''Handle authentication information for use with Planet APIs.'''

    @staticmethod
    def from_key(key: str) -> AuthType:
        '''Obtain authentication from api key.

        Parameters:
            key: Planet API key
        '''
        auth = APIKeyAuth(key=key)
        LOGGER.debug('Auth obtained from api key.')
        return auth

    @staticmethod
    def from_file(
        filename: Optional[typing.Union[str,
                                        pathlib.Path]] = None) -> AuthType:
        '''Create authentication from secret file.

        The secret file is named `.planet.json` and is stored in the user
        directory. The file has a special format and should have been created
        with `Auth.write()`.

        Parameters:
            filename: Alternate path for the planet secret file.

        '''
        filename = filename or SECRET_FILE_PATH

        try:
            secrets = _SecretFile(filename).read()
            auth = APIKeyAuth.from_dict(secrets)
        except FileNotFoundError:
            raise AuthException(f'File {filename} does not exist.')
        except (KeyError, json.decoder.JSONDecodeError):
            raise AuthException(f'File {filename} is not the correct format.')

        LOGGER.debug(f'Auth read from secret file {filename}.')
        return auth

    @staticmethod
    def from_env(variable_name: Optional[str] = None) -> AuthType:
        '''Create authentication from environment variable.

        Reads the `PL_API_KEY` environment variable

        Parameters:
            variable_name: Alternate environment variable.
        '''
        variable_name = variable_name or ENV_API_KEY
        api_key = os.getenv(variable_name, '')
        try:
            auth = APIKeyAuth(api_key)
            LOGGER.debug(f'Auth set from environment variable {variable_name}')
        except APIKeyAuthException:
            raise AuthException(
                f'Environment variable {variable_name} either does not exist '
                'or is empty.')
        return auth

    @staticmethod
    def from_login(email: str,
                   password: str,
                   base_url: Optional[str] = None) -> AuthType:
        '''Create authentication from login email and password.

        Note: To keep your password secure, the use of `getpass` is
        recommended.

        Parameters:
            email: Planet account email address.
            password: Planet account password.
            base_url: The base URL to use. Defaults to production
                authentication API base url.
        '''
        cl = AuthClient(base_url=base_url)
        auth_data = cl.login(email, password)

        api_key = auth_data['api_key']
        auth = APIKeyAuth(api_key)
        LOGGER.debug('Auth set from login email and password')
        return auth

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: dict) -> AuthType:
        pass

    @property
    @abc.abstractmethod
    def value(self):
        pass

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass

    def store(self,
              filename: Optional[typing.Union[str, pathlib.Path]] = None):
        '''Store authentication information in secret file.

        Parameters:
            filename: Alternate path for the planet secret file.
        '''
        filename = filename or SECRET_FILE_PATH
        secret_file = _SecretFile(filename)
        secret_file.write(self.to_dict())


class AuthClient:

    def __init__(self, base_url: Optional[str] = None):
        """
        Parameters:
            base_url: The base URL to use. Defaults to production
                authentication API base url.
        """
        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def login(self, email: str, password: str) -> dict:
        '''Login using email identity and credentials.

        Note: To keep your password secure, the use of `getpass` is
        recommended.

        Parameters:
            email: Planet account email address.
            password:  Planet account password.

        Returns:
             A JSON object containing an `api_key` property with the user's
        API_KEY.
        '''
        url = f'{self._base_url}/login'
        data = {'email': email, 'password': password}

        sess = http.AuthSession()
        resp = sess.request(url=url, method='POST', json=data)
        return self.decode_response(resp)

    @staticmethod
    def decode_response(response):
        '''Decode the token JWT'''
        token = response.json()['token']
        return jwt.decode(token, options={'verify_signature': False})


class APIKeyAuthException(Exception):
    '''exceptions thrown by APIKeyAuth'''
    pass


class APIKeyAuth(httpx.BasicAuth, Auth):
    '''Planet API Key authentication.'''
    DICT_KEY = 'key'

    def __init__(self, key: str):
        '''Initialize APIKeyAuth.

        Parameters:
            key: API key.

        Raises:
            APIKeyException: If API key is None or empty string.
        '''
        if not key:
            raise APIKeyAuthException('API key cannot be empty.')
        self._key = key
        super().__init__(self._key, '')

    @classmethod
    def from_dict(cls, data: dict) -> APIKeyAuth:
        '''Instantiate APIKeyAuth from a dict.'''
        api_key = data[cls.DICT_KEY]
        return cls(api_key)

    def to_dict(self):
        '''Represent APIKeyAuth as a dict.'''
        return {self.DICT_KEY: self._key}

    @property
    def value(self):
        return self._key


class _SecretFile:

    def __init__(self, path: typing.Union[str, pathlib.Path]):
        self.path = pathlib.Path(path)

        self.permissions = stat.S_IRUSR | stat.S_IWUSR  # user rw

        # in sdk versions <=2.0.0, secret file was created with the wrong
        # permissions, fix this automatically as well as catching the unlikely
        # cases where the permissions get changed externally
        self._enforce_permissions()

    def write(self, contents: dict):
        try:
            secrets_to_write = self.read()
            secrets_to_write.update(contents)
        except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            secrets_to_write = contents

        self._write(secrets_to_write)

    def _write(self, contents: dict):
        LOGGER.debug(f'Writing to {self.path}')

        def opener(path, flags):
            return os.open(path, flags, self.permissions)

        with open(self.path, 'w', opener=opener) as fp:
            fp.write(json.dumps(contents))

    def read(self) -> dict:
        LOGGER.debug(f'Reading from {self.path}')
        with open(self.path, 'r') as fp:
            contents = json.loads(fp.read())
        return contents

    def _enforce_permissions(self):
        '''if the file's permissions are not what they should be, fix them'''
        try:
            # in octal, permissions is the last three bits of the mode
            file_permissions = self.path.stat().st_mode & 0o777
            if file_permissions != self.permissions:
                LOGGER.debug(
                    f'{self.path} permissions are {oct(file_permissions)}, '
                    f'should be {oct(self.permissions)}. Fixing.')
                self.path.chmod(self.permissions)
        except FileNotFoundError:
            # just skip it if the secret file doesn't exist
            pass
