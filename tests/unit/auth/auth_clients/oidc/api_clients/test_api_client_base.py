import json
import unittest

from requests.models import Response
from unittest import mock

from planet.auth.oidc.api_clients.api_client import OIDCAPIClient, \
    OIDCAPIClientException

TEST_API_ENDPOINT = 'https://blackhole.unittest.planet.com/api'
TEST_DATA1 = {"key1": "value1"}


def mocked_requests_get_or_post(request_url, **kwargs):
    response = Response()
    response.status_code = 200
    # request_url = kwargs.get('url', None)
    request_params = kwargs.get('params', None)
    request_data = kwargs.get('data', None)

    if request_url == TEST_API_ENDPOINT + '/data1.json':
        response.headers['content-type'] = 'application/json'
        response._content = str.encode(json.dumps(TEST_DATA1))
    elif request_url == TEST_API_ENDPOINT + '/data2.dat':
        response.headers['content-type'] = 'data/test'
        response._content = b'1234567890'
    elif request_url == TEST_API_ENDPOINT + '/reflect1.json':
        # for reflecting from params
        response._content = str.encode(
            json.dumps(request_params.get('reflect_data')))
        response.status_code = request_params.get('status_code')
    elif request_url == TEST_API_ENDPOINT + '/reflect2.json':
        # for reflecting from data
        response._content = str.encode(
            json.dumps(request_data.get('reflect_data')))
        response.status_code = request_data.get('status_code')
    elif request_url == TEST_API_ENDPOINT + '/oidc_error_1.json':
        response.headers['content-type'] = 'application/json'
        response._content = str.encode(
            json.dumps({
                "error": "TEST_ERROR",
                "error_description": "This is a test error"
            }))
    elif request_url == TEST_API_ENDPOINT + '/oidc_error_2.json':
        response.headers['content-type'] = 'application/json'
        response._content = str.encode(
            json.dumps({
                "errorCode": "TEST_ERROR",
                "errorSummary": "This is a test error"
            }))
    elif request_url == TEST_API_ENDPOINT + '/empty_json.json':
        response.headers['content-type'] = 'application/json'
        response._content = None
    else:
        response.status_code = 404
    return response


class ApiClientBaseTest(unittest.TestCase):

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_valid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/reflect1.json')
        under_test._checked_get(params={
            'status_code': 200, 'reflect_data': 'test_data'
        },
                                request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_invalid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/reflect1.json')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get(params={
                'status_code': 401, 'reflect_data': 'test_data'
            },
                                    request_auth=None)

    @mock.patch('requests.post', side_effect=mocked_requests_get_or_post)
    def test_checked_post_valid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/reflect2.json')
        under_test._checked_post(params={
            'status_code': 200, 'reflect_data': 'test_data'
        },
                                 request_auth=None)

    @mock.patch('requests.post', side_effect=mocked_requests_get_or_post)
    def test_checked_post_invalid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/reflect2.json')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_post(params={
                'status_code': 401, 'reflect_data': 'test_data'
            },
                                     request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_json_response_valid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/data1.json')
        json_response = under_test._checked_get_json_response(
            params=None, request_auth=None)
        self.assertEqual(TEST_DATA1, json_response)

    @mock.patch('requests.post', side_effect=mocked_requests_get_or_post)
    def test_checked_post_json_response_valid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/data1.json')
        json_response = under_test._checked_post_json_response(
            params=None, request_auth=None)
        self.assertEqual(TEST_DATA1, json_response)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_json_response_invalid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/data2.dat')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)

    @mock.patch('requests.post', side_effect=mocked_requests_get_or_post)
    def test_checked_post_json_response_invalid(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/data2.dat')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_post_json_response(params=None,
                                                   request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_json_response_invalid_empty(self, mock_get):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/empty_json.json')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_checked_get_json_response_invalid_not_found(self, mock_get):

        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/not_found')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_check_oidc_error_1(self, get_mock):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/oidc_error_1.json')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_check_oidc_error_2(self, get_mock):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/oidc_error_2.json')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)

    @mock.patch('requests.get', side_effect=mocked_requests_get_or_post)
    def test_check_oidc_error_content_type(self, get_mock):
        under_test = OIDCAPIClient(endpoint_uri=TEST_API_ENDPOINT +
                                   '/data2.dat')
        with self.assertRaises(OIDCAPIClientException):
            under_test._checked_get_json_response(params=None,
                                                  request_auth=None)
