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

import logging
import os
import re
import threading
import time
from requests_futures.sessions import FuturesSession
from requests import Request
from requests import Session
from . utils import check_status
from . models import Response
from . exceptions import InvalidAPIKey
from . exceptions import TooManyRequests
from . __version__ import __version__
from requests.compat import urlparse


USE_STRICT_SSL = not (os.getenv('DISABLE_STRICT_SSL', '').lower() == 'true')

log = logging.getLogger(__name__)


def _log_request(req):
    log.info('%s %s %s %s', req.method, req.url, req.params, req.data)


def _is_subdomain_of_tld(url1, url2):
    orig_host = urlparse(url1).hostname
    re_host = urlparse(url2).hostname
    return orig_host.split('.')[-2:] == re_host.split('.')[-2:]


class _Throttler(object):
    '''A context manager that allows at most ops/sec
    to avoid request throttling for all client operations.
    '''

    def __init__(self, ops=4):
        self._cond = threading.Semaphore()
        self._wait = 1./ops

    def __enter__(self):
        self._cond.acquire()
        self._t = time.time()

    def __exit__(self, *exc):
        w = self._wait - (time.time() - self._t)
        if w > 0:
            time.sleep(w)
        self._cond.release()
        return False

    def wrap(self, f):
        def w(*a, **kw):
            with self:
                return f(*a, **kw)
        return w


class RedirectSession(Session):
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


def _get_user_agent():
    return 'planet-client-python/%s' % __version__


def _headers(request):
    headers = {}
    if request.data:
        headers['Content-Type'] = 'application/json'
    if request.auth:
        headers.update({
            'Authorization': 'api-key %s' % request.auth.value
        })
    else:
        raise InvalidAPIKey('No API key provided')
    return headers


def _do_request(sess, req, **kwargs):
    for i in range(5):
        try:
            _log_request(req)
            t = time.time()
            resp = sess.request(
                req.method, req.url, data=req.data, headers=_headers(req),
                params=req.params, verify=USE_STRICT_SSL, **kwargs
            )
            # futures session returns futures so only check actual responses
            # for futures these will be checked in the wrapper model
            if hasattr(resp, 'status_code'):
                check_status(resp)
                # only log non-async calls
                log.debug('request took %.03f', time.time() - t)
            return resp
        except TooManyRequests:
            time.sleep(1)
    raise Exception('too many throttles, giving up')


class RequestsDispatcher(object):

    def __init__(self, workers=4):
        # general session for sync api calls
        self.session = RedirectSession()
        self.session.headers.update({'User-Agent': _get_user_agent()})
        # ensure all calls to the session are throttled
        self.session.request = _Throttler().wrap(self.session.request)
        # the asyncpool is reserved for long-running async tasks
        self._asyncpool = FuturesSession(
            max_workers=workers,
            session=self.session)

    def response(self, request):
        return Response(request, self)

    def _dispatch_async(self, request, callback):
        return _do_request(self._asyncpool, request, stream=True,
                           background_callback=callback)

    def _dispatch(self, request, callback=None):
        return _do_request(self.session, request)

    # @todo delete me w/ v0 removal
    def dispatch_request(self, method, url, auth=None, params=None, data=None):
        headers = {}
        content_type = 'application/json'
        if auth:
            headers.update({
                'Authorization': 'api-key %s' % auth.value,
                'Content-Type': content_type
            })
        req = Request(method, url, params=params, data=data, headers=headers)
        _log_request(req)
        return self.session.send(req.prepare(), verify=USE_STRICT_SSL)
