'''Test the low-level client up to the request/response level. That is, verify
a request is made to the expected URL and the response is as provided. Unless
specifically needed (e.g., JSON format), the response content should not
matter'''
from planet import api
import requests_mock


client = api.Client()
client.api_key = 'foobar'


def mockget(path, data, status_code=200):
    def outer(func):
        @requests_mock.mock()
        def inner(m):
            m.register_uri('GET', client.base_url + path,
                           text=data, status_code=status_code)
            func()
        return inner
    return outer


def assert_client_exc(clz, msg, status=None):
    try:
        client._get('whatevs')
    except clz, ex:
        assert msg == ex.message
    else:
        raise AssertionError('expected %s' % clz.__name__)


@mockget('whatevs', 'test', status_code=200)
def test_assert_client_exc_success():
    '''make sure our test works'''
    try:
        assert_client_exc(Exception, '')
        assert False
    except AssertionError, ae:
        assert ae.message == 'expected Exception'


@mockget('whatevs', 'test', status_code=400)
def test_assert_client_exc_fail():
    '''make sure our test works'''
    try:
        assert_client_exc(api.BadQuery, 'not test')
        assert False
    except AssertionError, ae:
        assert "'not test' == 'test'" in ae.message


def test_missing_api_key():
    client = api.Client()
    # make sure any detected key is cleared
    client.api_key = None

    def assert_missing():
        try:
            client._get('whatevs')
            assert False
        except api.InvalidAPIKey, ex:
            assert ex.message == 'No API key provided'
    assert_missing()
    client.api_key = ''
    assert_missing()


@mockget('whatevs', 'not exist', status_code=404)
def test_status_code_404():
    assert_client_exc(api.MissingResource, 'not exist')


@mockget('whatevs', 'emergency', status_code=911)
def test_status_code_other():
    assert_client_exc(api.APIException, '911: emergency')


@mockget('scenes', 'oranges')
def test_list_all_scene_types():
    assert client.list_all_scene_types().get_raw() == 'oranges'


@mockget('scenes/ortho/x22', 'bananas')
def test_fetch_scene_info_scene_id():
    assert client.fetch_scene_info('x22').get_raw() == 'bananas'
