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
import logging
import threading
import time
from .utils import write_to_file
from .models import RequestCancelled
try:
    import Queue as queue
except:
    # renamed in 3
    import queue


def _by_status(assets, types, status):
    return [assets[t] for t in types if
            t in assets and assets[t]['status'] == status]


def _all_status(assets, types, status):
    return all([assets[t]['status'] == status for t in types if t in assets])


def _debug(msg, *args):
    logging.debug(msg, *args)


class _Stage(object):
    '''A _Stage performs some sequence in an activate/poll/download cycle.

    The stage will first attempt to process any existing tasks and if there
    is capacity, poll for another from the iterator-like source (a _Stage is
    one, itself). If the response is False, this implies the source is
    exhausted or cancelled. If the response is None, there are no pending
    tasks from the source.

    When a _Stage has completed a task, it places the output in _results so
    they are available. If the task needs repeating, it is placed back in the
    task queue.

    A _Stage may perform a maximum number of do-per-seconds to avoid throttling
    The current approach is conservative and does not issue RPS but instead
    throttles if a request complets in under the allotted time.

    The Downloader uses the following stages:

    search-iter -> activation -> polling -> download

    Downloader syncrhronously drains the download stage allowing for completion
    and cancellation of any in-flight backgrounded requests.

    Where search-iter is an endless iterator of 'item' features from the API.

    This approach allows for back-pressure from constrained stages as well as
    re-queueing tasks without being deadlock prone (e.g. pull vs. push) and
    simplifies cancellation of the entire pipeline.
    '''
    def __init__(self, source, size=0, max_dps=0):
        self._source = source
        self._running = True
        self._size = size
        self._tasks = []
        # track the current task
        self._doing = None
        self._results = queue.Queue()
        self._min_sleep = 1. / max_dps if max_dps else 0
        threading.Thread(target=self._run).start()

    def next(self):
        try:
            # @todo to avoid blocking, possible to feed sentinel None/False?
            return self._results.get(timeout=1)
        except queue.Empty:
            if not self._alive():
                return False

    def cancel(self):
        # this makes us not alive
        self._running = False
        self._tasks = []

    def _task(self, t):
        return t

    def _alive(self):
        # alive means upstream source has pending stuff or neither upstream
        # or this stage have been cancelled or we have some pending tasks
        # in the case upstream is done, but we're not
        return self._running or len(self._tasks) or self._doing

    def _run(self):
        while self._alive():
            t = time.time()
            if self._tasks:
                self._doing = self._tasks.pop(0)
                self._do(self._doing)
                self._doing = None
            # if there is capacity and upstream or us is 'on', try to get
            # another task from upstream
            if len(self._tasks) < self._size and self._running:
                try:
                    # @todo minor refactor
                    # bleh, next wants an iterator, not just a __next__
                    if hasattr(self._source, 'next'):
                        n = self._source.next()
                    else:
                        n = next(self._source)
                except StopIteration:
                    n = False
                if n is False:
                    self._running = False
                elif n is not None:
                    n = self._task(n)
                    n and self._tasks.append(n)
            # note - this is conservative compared to timer invocation. we are
            # allowing _at most_ 1 'do' per min_sleep
            wait = self._min_sleep - (time.time() - t)
            if wait > 0 and self._running:
                _debug('sleep for %d', wait)
                time.sleep(wait)


class _AStage(_Stage):
    def __init__(self, source, client, asset_types):
        _Stage.__init__(self, source, 100, max_dps=5)
        self._client = client
        self._asset_types = asset_types

    def _do(self, item):
        assets = self._client.get_assets(item).get()
        if not any([t in assets for t in self._asset_types]):
            _debug('no desired assets in item, skipping')
            return
        inactive = _by_status(assets, self._asset_types, 'inactive')
        if inactive:
            # still need activation, try the first inactive
            self._client.activate(inactive[0])
            self._tasks.append(item)
            return

        if _all_status(assets, self._asset_types, 'activating') or \
           _all_status(assets, self._asset_types, 'active'):
            self._results.put((item, assets))
        else:
            # hmmm
            status = [assets[t]['status'] for t in self._asset_types]
            raise Exception('unexpected state %s' % status)


class _PStage(_Stage):
    def __init__(self, source, client, asset_types):
        _Stage.__init__(self, source, 100, max_dps=0)
        self._client = client
        self._asset_types = asset_types
        self._min_sleep = 5

    def _task(self, t):
        item, assets = t
        return item, assets, time.time()

    def _do(self, task):
        item, assets, start = task
        # if everything is ready, don't poll again, just pass on to results
        if _all_status(assets, self._asset_types, 'active'):
            self._results.put((item, assets))
            return
        assets = self._client.get_assets(item).get()
        if _all_status(assets, self._asset_types, 'active'):
            _debug('activation took %d', time.time() - start)
            self._results.put((item, assets))
        else:
            self._tasks.append((item, assets, start))


class _DStage(_Stage):
    def __init__(self, source, client, asset_types, dest):
        _Stage.__init__(self, source, 100, max_dps=2)
        self._client = client
        self._asset_types = asset_types
        self._dest = dest

    def _task(self, t):
        item, assets = t
        for at in self._asset_types:
            self._tasks.append((item, assets[at]))

    def _get_writer(self, item, asset):
        return write_to_file(self._dest)

    def _do(self, task):
        item, asset = task
        dl = self._client.download(
            asset, self._get_writer(item, asset))
        self._results.put((item, asset, dl))


class _Downloader(object):
    def __init__(self, client, asset_types, dest, **opts):
        self.client = client
        self.asset_types = asset_types
        self.dest = dest
        self._running = True
        self._opts = opts
        self._awaiting = None

    def _apply_opts(self, to):
        opts = self._opts
        opt = opts.pop('no_sleep', False)
        if opt:
            for s in self._stages:
                s._min_sleep = 0
        for k in opts:
            v, a = k.split('_')
            t = to.get(v, None)
            if t is None:
                logging.warn('option not supported %s', k)
            else:
                setattr(t, a, opts[k])

    def download(self, items):
        # build pipeline
        client, asset_types = self.client, self.asset_types
        astage = _AStage(items, client, asset_types)
        pstage = _PStage(astage, client, asset_types)
        dstage = _DStage(pstage, client, asset_types, self.dest)
        self._stages = astage, pstage, dstage

        # sneaky little hack to allow tests to inject options
        self._apply_opts(vars())

        # poll download for futures to await - at this point these have
        # all been backgrounded and are likely actively streaming
        # this means any in-flight temp files will be cleaned up as well
        while self._running:
            try:
                n = dstage.next()
                if n is False:
                    break
                if n:
                    # while awaiting, store a ref since to allow cancelling
                    self._awaiting = n[2]
                    self._awaiting.await()
            except StopIteration:
                break
            except RequestCancelled:
                # this is async from cancelling the body write
                break

    def shutdown(self):
        self._running = False
        # if there is a pending future, cancel it, see above
        self._awaiting and self._awaiting.cancel()
        for s in self._stages:
            s.cancel()


downloader = _Downloader
