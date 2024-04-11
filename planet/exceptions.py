# Copyright 2015 Planet Labs, Inc.
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


class PlanetError(Exception):
    """Root for all exceptions thrown by the SDK"""
    pass


class APIError(PlanetError):
    """General unexpected API response"""


class BadQuery(APIError):
    """Invalid inputs, HTTP 400"""
    pass


class InvalidAPIKey(APIError):
    """Invalid key, HTTP 401"""
    pass


class NoPermission(APIError):
    """Insufficient permissions, HTTP 403"""
    pass


class MissingResource(APIError):
    """Request for non existing resource, HTTP 404"""
    pass


class Conflict(APIError):
    """Request conflict with current state of the target resource, HTTP 409"""
    pass


class TooManyRequests(APIError):
    """Too many requests, HTTP 429"""
    pass


class OverQuota(APIError):
    """Quota exceeded, HTTP 429"""
    pass


class ServerError(APIError):
    """Unexpected internal server error, HTTP 500"""
    pass


class BadGateway(APIError):
    """Bad gateway, HTTP 502"""
    pass


class InvalidIdentity(APIError):
    """Raised when logging in with invalid credentials"""
    pass


class ClientError(PlanetError):
    """Exceptions thrown client-side"""
    pass


class AuthException(ClientError):
    """Exceptions encountered during authentication"""
    pass


class PagingError(ClientError):
    """For errors that occur during paging."""
    pass


class GeoJSONError(ClientError):
    """Errors that occur due to invalid GeoJSON"""


class FeatureError(ClientError):
    """Errors that occur due to incorrectly formatted feature reference"""
