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

from requests_futures.sessions import FuturesSession
from . utils import check_status
from . models import Response
from . exceptions import InvalidAPIKey


class RequestsDispatcher(object):

    def __init__(self, workers=4):
        self.session = FuturesSession(max_workers=workers)

    def response(self, request):
        return Response(request, self)

    def _dispatch_async(self, request, callback):
        auth = request.auth
        if not auth:
            raise InvalidAPIKey('No API key provided')
        self.session.headers.update({
            'Authorization': 'api-key %s' % auth.value
        })
        return self.session.get(request.url, params=request.params,
                                stream=True, background_callback=callback)

    def _dispatch(self, request, callback=None):
        response = self._dispatch_async(request, callback).result()
        check_status(response)
        return response
