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


_debug = logging.debug
_info = logging.info


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

    Downloader synchronously drains the download stage allowing for completion
    and cancellation of any in-flight backgrounded requests.

    Where search-iter is an endless iterator of 'item' features from the API.

    This approach allows for back-pressure from constrained stages as well as
    re-queueing tasks without being deadlock prone (e.g. pull vs. push) and
    simplifies cancellation of the entire pipeline.
    '''
    def __init__(self, source, size=0, max_dps=0):
        self._source = source
        self._running = True
        self._cancelled = False
        self._size = size
        self._tasks = []
        # track the current task
        self._doing = None
        self._results = queue.Queue()
        self._min_sleep = 1. / max_dps if max_dps else 0
        self._cond = threading.Condition()

    def __len__(self):
        return len(self._tasks) + (1 if self._doing else 0)

    def start(self):
        threading.Thread(target=self._run).start()

    def next(self):
        try:
            return self._results.get(timeout=.1)
        except queue.Empty:
            if not self._alive():
                return False

    def _i(self, msg, *args):
        _info(type(self).__name__ + ' : ' + msg, *args)

    def _cancel(self, result):
        pass

    def cancel(self):
        # this makes us not alive
        self._cancelled = True
        self._running = False
        self._tasks = []
        self._doing = None
        # drain any results and cancel them
        while not self._results.empty():
            r = self._results.get()
            r and self._cancel(r)
        # poison the results queue with sentinel
        self._results.put(False)
        # notify any sleepers
        try:
            self._cond.acquire()
            self._cond.notify_all()
        finally:
            self._cond.release()

    def _task(self, t):
        return t

    def _alive(self):
        # alive means upstream source has pending stuff or neither upstream
        # or this stage have been cancelled or we have some pending tasks
        # in the case upstream is done, but we're not
        return not self._cancelled and (
            self._running or len(self._tasks) or self._doing
        )

    def _run(self):
        while self._alive():
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
                # upstream is done if False
                self._running = n is not False
                # if not None (results pending), queue at head
                if n:
                    n = self._task(n)
                    n and self._tasks.insert(0, n)
            # if there is a task, run it
            if self._tasks:
                t = time.time()
                self._doing = self._tasks.pop(0)
                try:
                    self._do(self._doing)
                except Exception:
                    # @todo should cancel the entire process?
                    self._running = False
                    logging.exception('unexpected error in %s', self)
                    return
                self._doing = None
                # note - this is conservative compared to timer invocation.
                # allow _at most_ 1 'do' per min_sleep
                wait = self._min_sleep - (time.time() - t)
                if wait > 0 and not self._cancelled:
                    _info('sleep for %.2f', wait)
                    # waiting on the condition allows interrupting sleep
                    self._cond.acquire()
                    self._cond.wait(wait)
                    self._cond.release()


class _AStage(_Stage):
    def __init__(self, source, client, asset_types):
        _Stage.__init__(self, source, 100, max_dps=5)
        self._client = client
        self._asset_types = asset_types

    def _do(self, item):
        assets = self._client.get_assets(item).get()
        if not any([t in assets for t in self._asset_types]):
            _info('no desired assets in item, skipping')
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
    _min_poll_interval = 5

    def __init__(self, source, client, asset_types):
        _Stage.__init__(self, source, 100, max_dps=2)
        self._client = client
        self._asset_types = asset_types

    def _task(self, t):
        item, assets = t
        now = time.time()
        return item, assets, now, now

    def _do(self, task):
        item, assets, start, last = task
        now = time.time()
        # don't poll until min interval elapsed
        if now - last > self._min_poll_interval:
            assets = self._client.get_assets(item).get()
            last = now
        if _all_status(assets, self._asset_types, 'active'):
            _debug('activation took %d', time.time() - start)
            self._results.put((item, assets))
        else:
            self._tasks.append((item, assets, start, last))


class _DStage(_Stage):
    def __init__(self, source, client, asset_types, dest):
        _Stage.__init__(self, source, 100, max_dps=2)
        self._client = client
        self._asset_types = asset_types
        self._dest = dest
        self._write_lock = threading.Lock()
        self._written = 0

    def _task(self, t):
        item, assets = t
        for at in self._asset_types:
            self._tasks.append((item, assets[at]))

    def _cancel(self, result):
        item, asset, dl = result
        dl.cancel()

    def _track_write(self, **kw):
        if 'skip' in kw:
            self._i('skipping download of %s, already exists', kw['skip'].name)
        else:
            with self._write_lock:
                self._written += kw.get('wrote', 0)

    def _get_writer(self, item, asset):
        return write_to_file(self._dest, self._track_write, overwrite=False)

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
        self._client = client
        self._running = True
        self._opts = opts
        self._awaiting = None
        self._completed = 0
        self._stages = None

    def _apply_opts(self, to):
        opts = self._opts
        opt = opts.pop('no_sleep', False)
        if opt:
            for s in self._stages:
                s._min_sleep = 0
        for k in opts:
            v, a = k.split('_', 1)
            t = to.get(v, None)
            if t is None:
                logging.warn('option not supported %s', k)
            else:
                setattr(t, a, opts[k])

    def stats(self):
        if not self._stages:
            return {}
        astage, pstage, dstage = self._stages
        mb_written = '%.2fMB' % (dstage._written / 1.0e6)
        return {
            'paging': astage._running,
            'activating': len(astage),
            'pending': len(pstage),
            'downloading': dstage._results.qsize() +
            (1 if self._awaiting else 0),
            'downloaded': self._completed,
            'total': mb_written,
        }

    def download(self, items):
        # build pipeline
        client, asset_types = self.client, self.asset_types
        astage = _AStage(items, client, asset_types)
        pstage = _PStage(astage, client, asset_types)
        dstage = _DStage(pstage, client, asset_types, self.dest)
        self._stages = astage, pstage, dstage

        # sneaky little hack to allow tests to inject options
        self._apply_opts(vars())

        [s.start() for s in self._stages]

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
                    self._completed += 1
                    self._awaiting = None
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
        self._client.shutdown()


downloader = _Downloader
