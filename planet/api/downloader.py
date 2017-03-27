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
import os
import threading
import time
from .utils import write_to_file
from planet.api.exceptions import RequestCancelled
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


_logger = logging.getLogger(__name__)
_debug = _logger.debug
_info = _logger.info


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

    Where search-iter is an iterator of 'item' features from the API.

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

    def work(self):
        return len(self._tasks) + (1 if self._doing else 0)

    def start(self):
        threading.Thread(target=self._run).start()

    def next(self):
        try:
            return self._results.get()
        except queue.Empty:
            if not self._alive():
                return False

    def _i(self, msg, *args):
        _info(type(self).__name__ + ' : ' + msg, *args)

    def _d(self, msg, *args):
        _debug(type(self).__name__ + ' : ' + msg, *args)

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
            self._results.get()
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

    def _capacity(self):
        return len(self._tasks) < self._size

    def _get_tasks(self):
        while self._capacity() and self._running:
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
            if n:
                n = self._task(n)
                n and self._tasks.insert(0, n)
            else:
                break

    def _process_task(self):
        if self._tasks:
            self._doing = self._tasks.pop(0)
            try:
                self._do(self._doing)
            except Exception:
                # @todo should cancel the entire process?
                self._running = False
                logging.exception('unexpected error in %s', self)
                return
            self._doing = None

    def _run(self):
        while self._alive():
            self._get_tasks()
            t = time.time()
            self._process_task()
            # note - this is conservative compared to timer invocation.
            # allow _at most_ 1 'do' per min_sleep
            wait = self._min_sleep - (time.time() - t)
            if wait > 0 and not self._cancelled:
                self._d('sleep for %.2f', wait)
                # waiting on the condition allows interrupting sleep
                self._cond.acquire()
                self._cond.wait(wait)
                self._cond.release()

        # sentinel value to indicate we're done
        self._results.put(False)


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
        # @todo max pool should reflect client workers
        _Stage.__init__(self, source, 4, max_dps=2)
        self._client = client
        self._asset_types = asset_types
        self._dest = dest
        self._write_lock = threading.Lock()
        self._written = 0
        self._downloads = 0

    def _task(self, t):
        item, assets = t
        for at in self._asset_types:
            self._tasks.append((item, assets[at]))

    def cancel(self):
        while not self._results.empty():
            try:
                r = self._results.get(block=False)
                if r:
                    item, asset, dl = r
                    dl.cancel()
            except queue.Empty:
                pass
        _Stage.cancel(self)

    def _write_tracker(self, item, asset):
        def _tracker(**kw):
            if 'skip' in kw:
                self._i('skipping download of %s, already exists',
                        kw['skip'].name)
            elif 'wrote' in kw:
                with self._write_lock:
                    self._written += kw['wrote']
        return _tracker

    def _get_writer(self, item, asset):
        return

    def _do(self, task):
        item, asset = task
        writer = write_to_file(
            self._dest, self._write_tracker(item, asset), overwrite=False)
        self._downloads += 1
        self._results.put((item, asset,
                           self._client.download(asset, writer)))


class Downloader(object):
    '''A Downloader manages activation and download of Item Assets from the
    Data API. A Downloader should only be processing one request to either
    `activate` or `download` at a time. These functions are synchronous and
    will return on completion. Completion of activation or download events
    can be tracked by changing the `on_complete` method of the Downloader while
    the `stats` function allows for polling of internal state.
    '''

    def shutdown(self):
        '''Halt execution.'''
        raise NotImplemented()

    def stats(self):
        '''Retrieve internal state of the Downloader.

        Returns a dict of state:

        - paging: `bool` indicating that search results are being processed
        - activating: `int` number of items in the inactive or activating state
        - downloading: `int` number of items actively downloading
        - downloaded: `string` representation of MB transferred
        - complete: `int` number of completed downloads
        - pending: `int` number of items awaiting download
        '''
        raise NotImplemented()

    def activate(self, items, asset_types):
        '''Request activation of specified asset_types for the sequence of
        items.

        :param items: a sequence of Item representations.
        :param asset_types list: list of asset-type (str)
        '''
        raise NotImplemented()

    def download(self, items, asset_types, dest):
        '''Request activation and download of specified asset_types for the
        sequence of items.

        :param items: a sequence of Item representations.
        :param asset_types list: list of asset-type (str)
        :param dest str: Download destination directory, must exist.
        '''
        raise NotImplemented()

    def on_complete(self, item, asset, path=None):
        '''Notification of processing an item's asset, invoked on completion of
        `activate` or `download`.

        :param item: The API representation of the item
        :param asset: The API representation of the asset
        :param path: If downloaded, the location of the downloaded asset,
                     otherwise None
        '''
        pass


class _Downloader(Downloader):
    def __init__(self, client, **opts):
        self._client = client
        self._opts = opts
        self._stages = []
        self._completed = 0
        self._awaiting = None

    def activate(self, items, asset_types):
        return self._run(items, asset_types)

    def download(self, items, asset_types, dest):
        return self._run(items, asset_types, dest)

    def _init(self, items, asset_types, dest):
        client = self._client
        astage = _AStage(items, client, asset_types)
        pstage = _PStage(astage, client, asset_types)
        self._stages = [
            astage,
            pstage
        ]
        if dest:
            dstage = _DStage(pstage, client, asset_types, dest)
            self._stages.append(dstage)
            self._dest = dest

        # sneaky little hack to allow tests to inject options
        self._apply_opts(vars())
        self._completed = 0

    def _run(self, items, asset_types, dest=None):
        if self._stages:
            raise Exception('already running')

        self._init(items, asset_types, dest)

        [s.start() for s in self._stages]

        last = self._stages[-1]
        while self._stages:
            try:
                n = last.next()
                if n is False:
                    break
                # this represents an activation completion, report
                # each requested item/asset combo
                # @todo hacky lack of internal structure in results
                if len(n) == 2:
                    item, assets = n
                    for a in asset_types:
                        self.on_complete(item, assets[a])
                # otherwise it is a download
                else:
                    item, asset, self._awaiting = n
                    try:
                        body = self._awaiting.await()
                        self._awaiting = None
                        dl = os.path.join(self._dest, body.name)
                        self.on_complete(item, asset, dl)
                    except RequestCancelled:
                        pass
                self._completed += 1
            except StopIteration:
                break
        stats = self.stats()
        self._stages = []
        return stats

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
                raise Exception('option not supported %s', k)
            else:
                setattr(t, a, opts[k])

    def stats(self):
        stats = {
            'paging': False,
            'activating': 0,
            'pending': 0,
            'complete': 0,
        }
        if len(self._stages) == 3:
            stats['downloading'] = 0
            stats['downloaded'] = '0.0MB'
        if not self._stages:
            return stats

        astage, pstage = self._stages[:2]
        dstage = None if len(self._stages) == 2 else self._stages[2]
        if dstage is not None:
            mb_written = '%.2fMB' % (dstage._written / 1.0e6)
            stats['downloading'] = dstage._downloads - self._completed
            stats['downloaded'] = mb_written
        stats['paging'] = astage._running
        stats['activating'] = astage.work() + pstage.work()
        stats['pending'] = (dstage.work() if dstage else 0)
        stats['complete'] = self._completed
        return stats

    def shutdown(self):
        for s in self._stages:
            s.cancel()
        self._awaiting and self._awaiting.cancel()
        self._stages = []
        self._client.shutdown()


def create(client, **kw):
    '''Create a Downloader with the provided client.'''
    return _Downloader(client, **kw)
