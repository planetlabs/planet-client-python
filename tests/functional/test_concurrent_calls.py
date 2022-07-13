import asyncio
import logging

import httpx
import pytest

import planet
from planet import data_filter, exceptions

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.parametrize('limit, num_concurrent', [(1000, 100), (100, 1000)])
@pytest.mark.parametrize('read_timeout', [10, 60])
@pytest.mark.parametrize('max_connections', [50, 100])
async def test_no_limiting_throttling(limit,
                                      num_concurrent,
                                      read_timeout,
                                      max_connections,
                                      monkeypatch):
    LOGGER.warning(
        'order: max_connections, read_timeout, limit, num_concurrent')

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=read_timeout,
                 max_connections=max_connections,
                 rate_limit=0,
                 max_active=0)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(1))
@pytest.mark.parametrize('limit, num_concurrent', [(10, 500)])
@pytest.mark.parametrize('read_timeout', [10, 30])
@pytest.mark.parametrize('max_connections', [100])
@pytest.mark.parametrize('max_active', [50, 100])
@pytest.mark.parametrize('rate_limit', [10, 9.8, 5, 4.5])
async def test_limiting_throttling(execution_number,
                                   limit,
                                   num_concurrent,
                                   read_timeout,
                                   max_connections,
                                   rate_limit,
                                   max_active,
                                   monkeypatch):
    # THIS WAS DOCUMENTED, save for posterity
    LOGGER.warning(
        'order: rate_limit, max_active, max_connections, read_timeout, limit, num_concurrent, execution_number'
    )

    async def _search(cl):
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=read_timeout,
                 max_connections=max_connections,
                 rate_limit=rate_limit,
                 max_active=max_active)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize('max_active', [50, 100])
# @pytest.mark.parametrize('max_active', [100])
@pytest.mark.parametrize('rate_limit', [15, 10, 5, 3])
# @pytest.mark.parametrize('limit, num_concurrent', [(100, 1000), (1000, 100)])
# @pytest.mark.parametrize('limit, num_concurrent', [(100, 1000)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 100)])
async def test_rate_limit_max_active(execution_number,
                                     limit,
                                     num_concurrent,
                                     rate_limit,
                                     max_active,
                                     monkeypatch):
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
                 max_connections=100,
                 rate_limit=rate_limit,
                 max_active=max_active)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize('max_active', [50, 100])
@pytest.mark.parametrize('rate_limit', [10, 5])  # [15, 10, 5, 3])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 1000), (1000, 100)])
async def test_max_active_limit_concurrent(execution_number,
                                           limit,
                                           num_concurrent,
                                           rate_limit,
                                           max_active,
                                           monkeypatch):
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        # raise Exception('whoa')
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    retry_exceptions = [
        httpx.ReadError, httpx.RemoteProtocolError, exceptions.TooManyRequests
    ]

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 max_connections=100,
                 rate_limit=rate_limit,
                 max_active=max_active,
                 retry_exceptions=retry_exceptions)


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(3))
# @pytest.mark.parametrize('max_active', [50, 100])
# @pytest.mark.parametrize('max_active', [100])
@pytest.mark.parametrize('rate_limit, max_active',
                         [(10, 50), (10, 100),
                          (0, 0)])  # , 5])  # [15, 10, 5, 3])
# @pytest.mark.parametrize('limit, num_concurrent', [(100, 1000), (1000, 100)])
@pytest.mark.parametrize('limit, num_concurrent', [(100, 1000)])
# @pytest.mark.parametrize('limit, num_concurrent', [(100, 100)])
async def test_speed_with_exceptions(execution_number,
                                     limit,
                                     num_concurrent,
                                     rate_limit,
                                     max_active,
                                     monkeypatch):
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        # raise Exception('whoa')
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 max_connections=100,
                 rate_limit=rate_limit,
                 max_active=max_active)


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
    LOGGER.warning(
        'order: limit, num_concurrent, rate_limit, max_active, execution_number'
    )

    async def _search(cl):
        # raise Exception('whoa')
        sfilter = data_filter.permission_filter()
        items = await cl.quick_search(['PSScene'], sfilter, limit=limit)
        return list([i async for i in items])

    await _runit(_search,
                 planet.DataClient,
                 monkeypatch,
                 num_concurrent=num_concurrent,
                 read_timeout=30,
                 max_connections=100,
                 rate_limit=rate_limit,
                 max_active=max_active)


async def _runit(func,
                 client,
                 monkeypatch,
                 num_concurrent,
                 read_timeout,
                 max_connections,
                 rate_limit,
                 max_active,
                 retry_exceptions=None):
    monkeypatch.setattr(planet.http, 'READ_TIMEOUT', read_timeout)
    monkeypatch.setattr(planet.http, 'MAX_CONNECTIONS', max_connections)
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
            from collections import Counter
            task_exceptions = Counter([type(e) for e in exceptions])
            LOGGER.warning(f'Task exceptions: {task_exceptions}')
            raise exceptions[0]
