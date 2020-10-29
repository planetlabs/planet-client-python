# Copyright 2017 Planet Labs, Inc.
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

'''Test the low-level client up to the request/response level. That is, verify
a request is made to the expected URL and the response is as provided. Unless
specifically needed (e.g., JSON format), the response content should not
matter'''

import base64
import json
import os

from planet import api
import pytest
import requests_mock

# have to clear in case key is picked up via env
if api.auth.ENV_KEY in os.environ:
    os.environ.pop(api.auth.ENV_KEY)
# and monkey patch the dot file to avoid picking an existing one up
api.utils._planet_json_file = lambda: '.whyyounameafilelikethis123'


@pytest.fixture()
def client():
    return api.ClientV1('foobar')


def test_assert_client_execution_success(client):
    '''verify simple mock success response'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'whatevs')
        m.get(uri, text='test', status_code=200)
        assert 'test' == client._get('whatevs').get_body().get_raw()


def test_missing_api_key():
    '''verify exception raised on missing API key'''
    client = api.ClientV1(api_key=None)
    try:
        client._get('whatevs').get_body()
    except api.exceptions.InvalidAPIKey as ex:
        assert str(ex) == 'No API key provided'
    else:
        assert False


def test_status_code_404(client):
    '''Verify 404 handling'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'whatevs')
        m.get(uri, text='test', status_code=404)
        try:
            client._get('whatevs').get_body()
        except api.exceptions.MissingResource as ex:
            assert str(ex) == 'test'
        else:
            assert False


def test_status_code_other(client):
    '''Verify other unexpected HTTP status codes'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'whatevs')
        # yep, this is totally made up
        m.get(uri, text='emergency', status_code=911)
        try:
            client._get('whatevs').get_body()
        except api.exceptions.APIException as ex:
            assert str(ex) == '911: emergency'
        else:
            assert False


def test_login(client):
    '''Verify login functionality'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'v0/auth/login')
        response = json.dumps({'api_key': 'foobar'}).encode('utf-8')
        b64 = base64.urlsafe_b64encode(response)
        response = 'whatever.%s.whatever' % b64.decode('utf-8')
        m.post(uri, text=response, status_code=200)
        resp = client.login('jimmy', 'crackcorn')
        assert resp['api_key'] == 'foobar'


def test_login_failure(client):
    '''Verify login functionality'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'v0/auth/login')
        response = json.dumps({'message': 'invalid'})
        m.post(uri, text=response, status_code=401)
        try:
            client.login('jimmy', 'crackcorn')
        except api.exceptions.InvalidIdentity as ex:
            assert str(ex) == 'invalid'
        else:
            assert False


def test_login_errors(client):
    '''Verify login functionality'''
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'v0/auth/login')
        response = 'An error occurred'
        m.post(uri, text=response, status_code=500)
        try:
            client.login('jimmy', 'crackcorn')
        except api.exceptions.APIException as ex:
            assert str(ex) == '500: %s' % response
        else:
            assert False


def test_create_search(client):
    with requests_mock.Mocker() as m:
        uri = os.path.join(client.base_url, 'data/v1/searches/')
        m.post(uri, text='{"ok": true}')
        resp = client.create_search('{"foobar": true}')
        assert resp.get()['ok']


def assert_simple_search_response(uri, func, arg, method):
    with requests_mock.Mocker() as m:
        mfunc = getattr(m, method)
        mfunc(uri, text='{"ok": true}')
        resp = func(arg)
        assert resp.get()['ok']
    with requests_mock.Mocker() as m:
        mfunc = getattr(m, method)
        mfunc(uri + "?_page_size=10", text='{"ok": true}', complete_qs=True)
        resp = func(arg, page_size=10)
        assert resp.get()['ok']
    with requests_mock.Mocker() as m:
        mfunc = getattr(m, method)
        mfunc(uri + "?_sort=foo", text='{"ok": true}', complete_qs=True)
        resp = func(arg, sort='foo')
        assert resp.get()['ok']


def test_quick_search(client):
    url = client.base_url + 'data/v1/quick-search'
    assert_simple_search_response(url, client.quick_search,
                                  '{"foo": True}', 'post')


def test_saved_search(client):
    url = client.base_url + 'data/v1/searches/the-id/results'
    assert_simple_search_response(url, client.saved_search,
                                  'the-id', 'get')


def assert_simple_request(uri, func, args, method='get', match=None):
    match = match or (lambda r: True)
    with requests_mock.Mocker() as m:
        getattr(m, method)(uri, additional_matcher=match, text='{"ok": true}')
        resp = func(*args)
        assert resp.get()['ok']
    return m


def test_get_item(client):
    url = client.base_url + 'data/v1/item-types/the-type/items/the-id'
    assert_simple_request(url, client.get_item, ('the-type', 'the-id'))


def test_get_assets(client):
    url = client.base_url + 'data/v1/item-types/the-type/items/the-id/assets'
    assert_simple_request(url, client.get_assets_by_id,
                          ('the-type', 'the-id'))


def test_get_searches(client):
    url = client.base_url + 'data/v1/searches/?search_type=saved'
    assert_simple_request(url, client.get_searches, ())


def test_stats(client):
    url = client.base_url + 'data/v1/stats'

    # check that the post body contains the patched in filter
    # see: client._patch_stats_request
    def match(req):
        body = req.json()
        return body['filter']['config'] == {'gt': '1970-01-01T00:00:00Z'}
    assert_simple_request(url, client.stats, ({'request': True},),
                          method='post', match=match)


def test_list_analytic_feeds(client):
    url = client.base_url + 'analytics/feeds'
    assert_simple_request(url,
                          client.list_analytic_feeds,
                          (False,))


def test_get_feed_info(client):
    url = client.base_url + 'analytics/feeds/feed-id'
    assert_simple_request(url,
                          client.get_feed_info,
                          ('feed-id',))


@pytest.mark.parametrize('feed_id', [None, 'feed-id'])
def test_list_analytic_subscriptions(client, feed_id):
    url = client.base_url + 'analytics/subscriptions'
    assert_simple_request(url,
                          client.list_analytic_subscriptions,
                          (feed_id,))


def test_get_subscription_info(client):
    url = client.base_url + 'analytics/subscriptions/sub-id'
    assert_simple_request(url,
                          client.get_subscription_info,
                          ('sub-id',))


def test_list_collections(client):
    url = client.base_url + 'analytics/collections'
    assert_simple_request(url,
                          client.list_analytic_collections,
                          ())


def test_get_collection_info(client):
    url = client.base_url + 'analytics/collections/sub-id'
    assert_simple_request(url,
                          client.get_collection_info,
                          ('sub-id',))


def test_list_features(client):
    url = client.base_url + 'analytics/collections/sub-id/items'
    assert_simple_request(url,
                          client.list_collection_features,
                          ('sub-id', None, None))


# only testing source-image-info here, the other types output a file
def test_get_associated_resource(client):
    sid = 'sub-id'
    fid = 'feature-id'
    rid = 'source-image-info'
    url = '{}analytics/collections/{}/items/{}/resources/{}'.format(
        client.base_url, sid, fid, rid
    )
    assert_simple_request(url,
                          client.get_associated_resource_for_analytic_feature,
                          (sid, fid, rid))
