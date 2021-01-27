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
# import io
import logging
import math
from mock import MagicMock
import os
from pathlib import Path

import pytest

from planet.api import models


LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mocked_request():
    return models.Request('url', 'auth')


def mock_http_response(json=None, iter_content=None, text=None):
    m = MagicMock(name='http_response')
    m.headers = {}
    m.json.return_value = json or {}
    m.aiter_content = iter_content
    m.text = text or ''
    return m


@pytest.mark.asyncio
async def test_StreamingBody_write_img(tmpdir, mocked_request, open_test_img):
    async def _aiter_bytes():
        data = open_test_img.read()
        v = memoryview(data)

        chunksize = 100
        for i in range(math.ceil(len(v)/(chunksize))):
            yield v[i*chunksize:min((i+1)*chunksize, len(v))]

    r = MagicMock(name='response')
    hr = MagicMock(name='http_response')
    hr.aiter_bytes = _aiter_bytes
    hr.num_bytes_downloaded = 0
    hr.response.headers['Content-Length'] = 527
    r.http_response = hr
    body = models.StreamingBody(r)

    filename = Path(str(tmpdir)) / 'test.tif'
    await body.write(filename, progress_bar=False)

    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 527
