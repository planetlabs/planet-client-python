# Copyright 2026 Planet Labs PBC.
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
import pytest

from planet import async_processing_request as apr
from planet.exceptions import ClientError

BUCKET = {'s3': {'url': 's3://b/p', 'iamRoleARN': 'arn:role'}}
GEOM = {'type': 'Point', 'coordinates': [1, 2]}


def test_build_request_evalscript():
    req = apr.build_request({'i': 1}, {'o': 1}, evalscript='//VERSION=3')
    assert req == {
        'input': {
            'i': 1
        }, 'output': {
            'o': 1
        }, 'evalscript': '//VERSION=3'
    }


def test_build_request_evalscript_reference():
    req = apr.build_request({}, {}, evalscript_reference=BUCKET)
    assert req['evalscriptReference'] == BUCKET
    assert 'evalscript' not in req


@pytest.mark.parametrize('kwargs',
                         [{}, {
                             'evalscript': 'x', 'evalscript_reference': BUCKET
                         }])
def test_build_request_evalscript_exclusive(kwargs):
    with pytest.raises(ClientError):
        apr.build_request({}, {}, **kwargs)


def test_process_input_bbox_geometry_crs():
    src = apr.data_source('sentinel-2-l2a')
    inp = apr.process_input([src],
                            bbox=[1, 2, 3, 4],
                            geometry=GEOM,
                            crs='EPSG')
    assert inp == {
        'bounds': {
            'bbox': [1, 2, 3, 4],
            'geometry': GEOM,
            'properties': {
                'crs': 'EPSG'
            }
        },
        'data': [src]
    }


def test_process_input_geometry_only():
    inp = apr.process_input([{'type': 't'}], geometry=GEOM)
    assert inp['bounds'] == {'geometry': GEOM}


@pytest.mark.parametrize('kwargs',
                         [
                             {
                                 'data': [{
                                     'type': 't'
                                 }]
                             },
                             {
                                 'data': [{
                                     'type': 't'
                                 }], 'bbox': [1, 2, 3]
                             },
                             {
                                 'data': [], 'bbox': [1, 2, 3, 4]
                             },
                         ])
def test_process_input_invalid(kwargs):
    with pytest.raises(ClientError):
        apr.process_input(**kwargs)


def test_data_source_minimal():
    assert apr.data_source('sentinel-1-grd') == {'type': 'sentinel-1-grd'}


def test_data_source_full():
    src = apr.data_source('sentinel-2-l2a',
                          time_from='2024-01-01T00:00:00Z',
                          time_to='2024-02-01T00:00:00Z',
                          max_cloud_coverage=20,
                          mosaicking_order='leastCC',
                          id='s2',
                          processing={'upsampling': 'BICUBIC'})
    assert src == {
        'type': 'sentinel-2-l2a',
        'id': 's2',
        'dataFilter': {
            'timeRange': {
                'from': '2024-01-01T00:00:00Z', 'to': '2024-02-01T00:00:00Z'
            },
            'maxCloudCoverage': 20,
            'mosaickingOrder': 'leastCC'
        },
        'processing': {
            'upsampling': 'BICUBIC'
        }
    }


def test_data_source_open_time_range():
    src = apr.data_source('t', time_to='2024-02-01T00:00:00Z')
    assert src['dataFilter'] == {'timeRange': {'to': '2024-02-01T00:00:00Z'}}


def test_process_output_size():
    out = apr.process_output(BUCKET,
                             width=100,
                             height=200,
                             responses=[apr.response()])
    assert out == {
        'width': 100,
        'height': 200,
        'responses': [{
            'identifier': 'default', 'format': {
                'type': 'image/tiff'
            }
        }],
        'delivery': BUCKET
    }


def test_process_output_resolution():
    out = apr.process_output(BUCKET, resx=10, resy=10)
    assert out == {'resx': 10, 'resy': 10, 'delivery': BUCKET}


@pytest.mark.parametrize('kwargs',
                         [
                             {
                                 'width': 1, 'height': 1, 'resx': 1, 'resy': 1
                             },
                             {
                                 'width': 1
                             },
                             {
                                 'resy': 1
                             },
                         ])
def test_process_output_invalid(kwargs):
    with pytest.raises(ClientError):
        apr.process_output(BUCKET, **kwargs)


def test_response():
    assert apr.response('userdata', 'application/json') == {
        'identifier': 'userdata', 'format': {
            'type': 'application/json'
        }
    }


def test_s3_bucket_role():
    assert apr.s3_bucket('s3://b/p', iam_role_arn='arn', region='us-east-1') \
        == {'s3': {'url': 's3://b/p', 'iamRoleARN': 'arn',
                   'region': 'us-east-1'}}


def test_s3_bucket_keys():
    assert apr.s3_bucket('s3://b', access_key='a', secret_access_key='s') \
        == {'s3': {'url': 's3://b', 'accessKey': 'a',
                   'secretAccessKey': 's'}}


@pytest.mark.parametrize('kwargs',
                         [
                             {
                                 'url': 'gs://b', 'iam_role_arn': 'arn'
                             },
                             {
                                 'url': 's3://b'
                             },
                             {
                                 'url': 's3://b', 'access_key': 'a'
                             },
                             {
                                 'url': 's3://b', 'secret_access_key': 's'
                             },
                         ])
def test_s3_bucket_invalid(kwargs):
    with pytest.raises(ClientError):
        apr.s3_bucket(**kwargs)


def test_gs_bucket():
    assert apr.gs_bucket('gs://b/p', 'Y3JlZHM=') == {
        'gs': {
            'url': 'gs://b/p', 'credentials': 'Y3JlZHM='
        }
    }


def test_gs_bucket_invalid():
    with pytest.raises(ClientError):
        apr.gs_bucket('s3://b', 'c')
