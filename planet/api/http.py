# Copyright 2020 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""Functionality to perform HTTP requests"""

# import http.client as http_client
import logging
import os
import re
import time

from requests import Session
from requests.compat import urlparse

from . import exceptions, models
from . __version__ import __version__


LOGGER = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 32 * 1024

USE_STRICT_SSL = not (os.getenv('DISABLE_STRICT_SSL', '').lower() == 'true')

RETRY_WAIT_TIME = 1  # seconds


# def setup_logging():
#     log_level = LOGGER.getEffectiveLevel()
#     urllib3_logger = logging.getLogger(
#         'requests.packages.urllib3')
#     urllib3_logger.setLevel(log_level)
#
#     # if debug level set then its nice to see the headers of the request
#     if log_level == logging.DEBUG:
#         http_client.HTTPConnection.set_debuglevel(1)
#     else:
#         http_client.HTTPConnection.set_debuglevel(0)
#

def _log_request(req):
    LOGGER.info('%s %s %s %s', req.method, req.url, req.params, req.data)


class PlanetSession(object):
    # TODO: update this documentation
    """A Planet API http session.

    Provides request/response communication with the planet API.

    Basic Usage::

      >>> ps = PlanetSession()
      >>> req = models.Request(url, auth)
      >>> ps.request(req, retry_count=5)
      <models.Response [200]>

    Or as a context manager::

      >>> with PlanetSession() as ps:
      ...     ps.request(req, retry_count=5)
      <models.Response [200]>
    """

    def __init__(self):
        # general session for sync api calls
        self._session = RedirectSession()
        self._session.headers.update({'User-Agent': self._get_user_agent()})
        self._session.verify = USE_STRICT_SSL
        self.retry_wait_time = RETRY_WAIT_TIME

    @staticmethod
    def _get_user_agent():
        return 'planet-client-python/' + __version__

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._session.close()

    def request(self, request, retry_count=5):
        '''Submit a request with retry.

        :param :py:Class:`planet.api.models.Request` req: request to submit
        :param int retry_count: number of retries
        :returns: :py:Class:`planet.api.models.Response`
        '''
        max_retry = retry_count + 1
        for i in range(max_retry):
            try:
                resp = self._do_request(request)
                return resp
            except exceptions.TooManyRequests:
                if i < max_retry:
                    LOGGER.debug('Try {}'.format(i))
                    LOGGER.info('Too Many Requests: sleeping and retrying')
                    # TODO: consider exponential backoff
                    # https://developers.planet.com/docs/data/api-mechanics/
                    time.sleep(self.retry_wait_time)
        raise Exception('too many throttles, giving up')

    def _do_request(self, request, **kwargs):
        '''Submit a request

        :param :py:Class:`planet.api.models.Request` req: request to submit
        :returns: :py:Class:`planet.api.models.Response`
        '''
        # TODO: I don't know where kwargs are used, maybe nowhere?
        LOGGER.debug('about to submit request')
        _log_request(request)

        t = time.time()
        http_resp = self._session.request(
            request.method, request.url, data=request.data,
            headers=request.headers, params=request.params)
        LOGGER.debug('request took %.03f', time.time() - t)

        resp = models.Response(request, http_resp)
        resp.raise_for_status()
        return resp


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
            if not self._is_subdomain_of_tld(orig, redir):
                prepared_request.headers.pop('Authorization')
                key = re.match(r'api-key (\S+)', existing_auth)
                if key:
                    prepared_request.prepare_url(
                        prepared_request.url, {
                            'api_key': key.group(1)
                        }
                    )

    @staticmethod
    def _is_subdomain_of_tld(url1, url2):
        orig_host = urlparse(url1).hostname
        re_host = urlparse(url2).hostname
        return orig_host.split('.')[-2:] == re_host.split('.')[-2:]
