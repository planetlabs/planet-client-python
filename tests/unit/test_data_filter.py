# Copyright 2020 Planet Labs PBC.
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
from datetime import datetime, timedelta, tzinfo
import logging
import pytest

from planet import data_filter, exceptions

LOGGER = logging.getLogger(__name__)


def test_and_filter():
    f1 = {'type': 'testf1'}
    f2 = {'type': 'testf2'}
    res = data_filter.and_filter([f1, f2])
    expected = {'type': 'AndFilter', 'config': [f1, f2]}
    assert res == expected


def test_or_filter():
    f1 = {'type': 'testf1'}
    f2 = {'type': 'testf2'}
    res = data_filter.or_filter([f1, f2])
    expected = {'type': 'OrFilter', 'config': [f1, f2]}
    assert res == expected


def test_not_filter():
    f1 = {'type': 'testf1'}
    res = data_filter.not_filter(f1)
    expected = {'type': 'NotFilter', 'config': f1}
    assert res == expected


def test_date_range_filter_basic():
    gt = datetime(2022, 5, 1, 1, 0, 0, 1)
    gte = datetime(2022, 5, 1, 1, 0, 1)
    lt = datetime(2022, 6, 1, 1, 1)
    lte = datetime(2022, 6, 1, 1)

    res = data_filter.date_range_filter('acquired',
                                        gt=gt,
                                        gte=gte,
                                        lt=lt,
                                        lte=lte)
    expected = {
        'type': 'DateRangeFilter',
        'field_name': 'acquired',
        'config': {
            'gt': '2022-05-01T01:00:00.000001Z',
            'gte': '2022-05-01T01:00:01Z',
            'lt': '2022-06-01T01:01:00Z',
            'lte': '2022-06-01T01:00:00Z',
        }
    }
    assert res == expected


def test_date_range_filter_timezone():
    # Make a concrete tzinfo class for testing
    # https://docs.python.org/3.7/library/datetime.html#datetime.tzinfo
    class TestTZ(tzinfo):

        def __init__(self, offset=None):
            self.offset = offset
            super().__init__()

        def utcoffset(self, dt):
            return timedelta(hours=self.offset) if self.offset else None

        def dt(self, dt):
            # a fixed-offset class:  doesn't account for DST
            return timedelta(0)

        def tzname(self, dt):
            return 'TestTZ'

    gt = datetime(2022, 6, 1, 1, tzinfo=TestTZ(0))
    lt = datetime(2022, 6, 1, 1, tzinfo=TestTZ(1))

    res = data_filter.date_range_filter('acquired', gt=gt, lt=lt)
    expected = {
        'type': 'DateRangeFilter',
        'field_name': 'acquired',
        'config': {
            'gt': '2022-06-01T01:00:00Z', 'lt': '2022-06-01T01:00:00+01:00'
        }
    }
    assert res == expected


def test_date_range_filter_failure():
    with pytest.raises(exceptions.PlanetError):
        data_filter.date_range_filter('acquired')
