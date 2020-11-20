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
from mock import Mock

import pytest
import requests_mock

from planet.api import http, models


TEST_URL = 'mock://fantastic.com'


@pytest.fixture
def mock_request():
    r = Mock()
    r.url = TEST_URL
    r.body_type = models.Body
    r.method = 'GET'
    r.headers = {}
    r.params = None
    r.data = None

    yield r


@pytest.fixture
def throttle_adapter():
    adapter = requests_mock.Adapter()
    responses = [
        {'json': {'msg': 'msg'}, 'status_code': 429},
        {'json': {'msg': 'msg'}, 'status_code': 200}
    ]
    adapter.register_uri('GET', TEST_URL, responses)
    yield adapter


def test_planetsession_contextmanager():
    with http.PlanetSession():
        pass


def test_planetsession_request_retry(mock_request, throttle_adapter):
    with http.PlanetSession() as ps:
        # needed to redirect calls to the adapter
        ps._session.mount('mock://', throttle_adapter)

        ps.retry_wait_time = 0  # lets not slow down tests for this
        resp = ps.request(mock_request)
        assert resp


def test_redirectsession_rebuilt_auth_called():
    '''verify our hacking around with Session behavior works'''
    session = http.RedirectSession()
    with requests_mock.Mocker() as m:
        m.get('http://redirect.com', status_code=302, headers={
            'Location': 'http://newredirect.com'
        })
        m.get('http://newredirect.com', text='redirected!')

        # base assertion, works as intended
        resp = session.get('http://redirect.com')
        assert resp.url == 'http://newredirect.com'
        assert resp.text == 'redirected!'

        # Authorization headers unpacked and URL is rewritten
        resp = session.get('http://redirect.com', headers={
            'Authorization': 'api-key foobar'
        })
        assert resp.url == 'http://newredirect.com/?api_key=foobar'
        assert resp.text == 'redirected!'

        # Authorization headers unpacked and URL is rewritten, params saved
        m.get('http://redirect.com', status_code=302, headers={
            'Location': 'http://newredirect.com?param=yep'
        })
        m.get('http://newredirect.com?param=yep', text='param!')
        resp = session.get('http://redirect.com?param=yep', headers={
            'Authorization': 'api-key foobar'
        })
        assert resp.url == 'http://newredirect.com/?param=yep&api_key=foobar'
        assert resp.text == 'param!'


def test_redirectsession_is_subdomain_of_tld():
    fcn = http.RedirectSession._is_subdomain_of_tld
    assert fcn('http://foo.bar', 'http://foo.bar')
    assert fcn('http://one.foo.bar', 'http://foo.bar')
    assert fcn('http://foo.bar', 'http://one.foo.bar')
    assert not fcn('http://foo.bar', 'http://bar.foo')
    assert not fcn('http://one.foo.bar', 'http://bar.foo')
    assert not fcn('http://foo.bar', 'http://one.bar.foo')
