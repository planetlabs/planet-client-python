import asyncio
from collections import Counter
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
    # Find configuration that successfully completes and runs the fastest
    # Setting rate_limit and max_active to zero disables limiting
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 rate_limit=rate_limit,
                 max_active=max_active)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(1))
@pytest.mark.parametrize('rate_limit, max_active', [(0, 0)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 3)])
async def test_api_rate_limiting(execution_number,
                                 limit,
                                 num_concurrent,
                                 rate_limit,
                                 max_active,
                                 monkeypatch):
    # Find configuration that successfully completes and runs the fastest
    # Setting rate_limit and max_active to zero disables limiting
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    monkeypatch.setattr(planet.http, 'RETRY_EXCEPTIONS', [])
    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 rate_limit=rate_limit,
                 max_active=max_active)


# @pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(20))
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
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
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
    cmds = [
        '--tb=line',
        '--log-format=%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
        '--log-date-format=%Y-%m-%d %H:%M:%S',
        '--log-cli-level=warning',
        '--durations=0',
        __file__
    ]

    extras = sys.argv[1:]
    cmds += extras
    print(cmds)
    sys.exit(pytest.main(cmds))
