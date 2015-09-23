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


class APIException(Exception):
    '''also used as placeholder for unexpected response status_code'''
    pass


class BadQuery(APIException):
    pass


class InvalidAPIKey(APIException):
    pass


class NoPermission(APIException):
    pass


class MissingResource(APIException):
    pass


class OverQuota(APIException):
    pass


class ServerError(APIException):
    pass


class InvalidIdentity(APIException):
    '''raised when logging in with identity'''
    pass


class RequestCancelled(Exception):
    '''When requests get cancelled'''
