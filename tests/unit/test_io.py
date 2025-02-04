# Copyright 2022 Planet Labs, PBC.
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
from datetime import datetime
import logging
import pytest

from planet import exceptions, io

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def make_aiter():

    async def func(values):
        for v in values:
            yield v

    return func


@pytest.mark.anyio
async def test_collect_non_features(make_aiter):
    values = [{
        'key11': 'value11', 'key12': 'value12'
    }, {
        'key21': 'value21', 'key22': 'value22'
    }]

    values_aiter = make_aiter(values)
    res = await io.collect(values_aiter)
    assert res == values


@pytest.mark.anyio
async def test_collect_features(feature_geojson, make_aiter):
    feature2 = feature_geojson.copy()
    feature2['properties'] = {'foo': 'bar'}
    values = [feature_geojson, feature2]
    values_aiter = make_aiter(values)

    res = await io.collect(values_aiter)
    expected = {'type': 'FeatureCollection', 'features': values}
    assert res == expected


@pytest.mark.parametrize(
    "string, expected",
    [
        # RFC 3339 string from API response
        ("2021-02-03T01:40:07.359Z", datetime(2021, 2, 3, 1, 40, 7, 359000)),
        # date-only ISO 8601
        ("2021-01-01", datetime(2021, 1, 1)),
        # date-time ISO 8601
        ("2021-01-01", datetime(2021, 1, 1))
    ])
def test_str_to_datetime_success(string, expected):
    assert io.str_to_datetime(string) == expected


def test_str_to_datetime_failure():
    with pytest.raises(exceptions.PlanetError):
        io.str_to_datetime('notadate')
