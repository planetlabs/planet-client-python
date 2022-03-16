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


class PlanetException(Exception):
    """Root for all exceptions thrown by the SDK"""
    pass


class APIException(PlanetException):
    '''General unexpected API response'''
    @property
    def message(self):
        return self.args[0]


class BadQuery(APIException):
    '''Invalid inputs, HTTP 400'''
    pass


class InvalidAPIKey(APIException):
    '''Invalid key, HTTP 401'''
    pass


class NoPermission(APIException):
    '''Insufficient permissions, HTTP 403'''
    pass


class MissingResource(APIException):
    '''Request for non existing resource, HTTP 404'''
    pass


class Conflict(APIException):
    '''Request conflict with current state of the target resource, HTTP 409'''
    pass


class TooManyRequests(APIException):
    '''Too many requests, HTTP 429'''
    pass


class OverQuota(APIException):
    '''Quota exceeded, HTTP 429'''
    pass


class ServerError(APIException):
    '''Unexpected internal server error, HTTP 500'''
    pass


class InvalidIdentity(APIException):
    '''Raised when logging in with invalid credentials'''
    pass


class ClientError(PlanetException):
    """Exceptions thrown client-side"""
    pass


class AuthException(ClientError):
    '''Exceptions encountered during authentication'''
    pass


class RequestCancelled(ClientError):
    '''Internal exception when a request is cancelled'''
    pass
