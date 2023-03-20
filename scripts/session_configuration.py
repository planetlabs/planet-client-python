# Copyright 2022 Planet Labs PBC.
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
"""Test Session Configuration.

This is a script for identifying the best session configuration for fast,
reliable, and polite communication with the Planet services.
"""
import argparse
import asyncio
from collections import Counter
import inspect
import logging
import sys

import pytest

import planet
from planet import data_filter

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize('rate_limit, max_active', [(10, 50), (10, 100),
                                                    (0, 0)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 3)])
async def test_configuration(execution_number,
                             limit,
                             num_concurrent,
                             rate_limit,
                             max_active,
                             monkeypatch):
    """Find configuration that successfully completes and runs the fastest"""
    # Setting rate_limit and max_active to zero disables limiting
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = cl.search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 rate_limit=rate_limit,
                 max_active=max_active)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize('rate_limit, max_active', [(0, 0)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 3)])
async def test_api_rate_limiting(execution_number,
                                 limit,
                                 num_concurrent,
                                 rate_limit,
                                 max_active,
                                 monkeypatch):
    """Test API rate limit behavior"""
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = cl.search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    monkeypatch.setattr(planet.http, 'RETRY_EXCEPTIONS', [])
    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 rate_limit=rate_limit,
                 max_active=max_active)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(5))
@pytest.mark.parametrize('rate_limit, max_active', [(10, 50)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 1000)])
async def test_reliability(execution_number,
                           limit,
                           num_concurrent,
                           rate_limit,
                           max_active,
                           monkeypatch):
    """Stress test the reliability of the communication with Planet services.
    """
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = cl.search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 rate_limit=rate_limit,
                 max_active=max_active)


async def _runit(func,
                 client,
                 monkeypatch,
                 num_concurrent,
                 read_timeout,
                 rate_limit,
                 max_active,
                 retry_exceptions=None):
    """Run a method of a client with different session settings"""
    monkeypatch.setattr(planet.http, 'READ_TIMEOUT', read_timeout)
    monkeypatch.setattr(planet.http, 'RATE_LIMIT', rate_limit)
    monkeypatch.setattr(planet.http, 'MAX_ACTIVE', max_active)

    if retry_exceptions:
        monkeypatch.setattr(planet.http, 'RETRY_EXCEPTIONS', retry_exceptions)

    async with planet.Session() as sess:
        cl = client(sess)
        tasks = [asyncio.create_task(func(cl)) for _ in range(num_concurrent)]

        res = await asyncio.gather(*tasks, return_exceptions=True)
        LOGGER.warning(f'Session outcomes: {sess.outcomes}')

        exceptions = [r for r in res if isinstance(r, BaseException)]
        if len(exceptions):
            task_exceptions = Counter([type(e) for e in exceptions])
            LOGGER.warning(f'Task exceptions: {task_exceptions}')
            raise exceptions[0]


if __name__ == "__main__":
    # automatically find the tests within this module for specifying as
    # possible choices for test argument
    this_module = sys.modules[__name__]
    test_options = [
        t[0] for t in inspect.getmembers(this_module, inspect.isfunction)
        if t[0].startswith('test_')
    ]

    log_levels = ('debug', 'info', 'warning', 'error', 'critical')

    parser = argparse.ArgumentParser(
        description='Session configuration tests.')
    parser.add_argument('--log-level', default='warning', choices=log_levels)
    parser.add_argument('test',
                        choices=test_options,
                        help='specify the test to run')
    args = parser.parse_args()

    cmds = [
        '--tb=line',  # we are only interested in the types of exceptions raised
        '--log-format=%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
        '--log-date-format=%Y-%m-%d %H:%M:%S',
        f'--log-cli-level={args.log_level}',
        '--durations=0',  # record and report runtimes
        __file__,
        f'-k={args.test}'
    ]
    print(f'Running: pytest {" ".join(cmds)}')
    sys.exit(pytest.main(cmds))
