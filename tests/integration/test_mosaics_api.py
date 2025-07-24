import asyncio
import functools
import inspect
from unittest.mock import patch
from planet.sync.mosaics import MosaicsAPI
from tests.integration import test_mosaics_cli
import pytest

from concurrent.futures import ThreadPoolExecutor


def async_wrap(api):
    pool = ThreadPoolExecutor()

    def make_async(fn):

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            future = pool.submit(fn, *args, **kwargs)
            res = await asyncio.wrap_future(future)
            if inspect.isgenerator(res):
                return list(res)
            return res

        return wrapper

    members = inspect.getmembers(api, inspect.isfunction)
    funcs = {m[0]: make_async(m[1]) for m in members if m[0][0] != "_"}
    funcs["__init__"] = getattr(api, "__init__")
    funcs["_pool"] = pool
    return type("AsyncAPI", (object, ), funcs)


# @pytest.mark.skip
@pytest.mark.parametrize(
    "tc", [pytest.param(tc, id=tc.id) for tc in test_mosaics_cli.test_cases])
def test_api(tc):
    api = async_wrap(MosaicsAPI)
    with patch('planet.cli.mosaics.MosaicsClient', api):
        test_mosaics_cli.run_test(tc)
        api._pool.shutdown()
