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

import re
from requests_futures.sessions import FuturesSession
from requests import Request
from . utils import check_status
from . models import Response
from . exceptions import InvalidAPIKey
from requests.compat import urlparse


def _is_subdomain_of_tld(url1, url2):
    orig_host = urlparse(url1).hostname
    re_host = urlparse(url2).hostname
    return orig_host.split('.')[-2:] == re_host.split('.')[-2:]


class RedirectSession(FuturesSession):
    '''This exists to override the existing behavior of requests that will
    strip Authorization headers from any redirect requests that resolve to a
    new domain. Instead, we'll keep headers if the redirect is a subdomain
    and if not, extract the api-key from the header and add it to the url
    as a parameter.
    '''
    def rebuild_auth(self, prepared_request, response):
        existing_auth = prepared_request.headers.get('Authorization', None)
        if existing_auth:
            orig = response.request.url
            redir = prepared_request.url
            if not _is_subdomain_of_tld(orig, redir):
                prepared_request.headers.pop('Authorization')
                key = re.match('api-key (\S+)', existing_auth)
                if key:
                    prepared_request.prepare_url(
                        prepared_request.url, {
                            'api_key': key.group(1)
                        }
                    )


class RequestsDispatcher(object):

    def __init__(self, workers=4):
        self.session = RedirectSession(max_workers=workers)

    def response(self, request):
        return Response(request, self)

    def _dispatch_async(self, request, callback):
        auth = request.auth
        if not auth:
            raise InvalidAPIKey('No API key provided')

        def _auth_callback(req):
            req.headers.update({
                'Authorization': 'api-key %s' % auth.value
            })
            return req

        return self.session.get(request.url, params=request.params,
                                stream=True, background_callback=callback,
                                auth=_auth_callback)

    def _dispatch(self, request, callback=None):
        response = self._dispatch_async(request, callback).result()
        check_status(response)
        return response

    def dispatch_request(self, method, url, auth=None, params=None, data=None):
        headers = {}
        content_type = 'application/json'
        if auth:
            headers.update({
                'Authorization': 'api-key %s' % auth.value,
                'content-Type': content_type
            })
        req = Request(method, url, params=params, data=data, headers=headers)
        return self.session.send(req.prepare())
