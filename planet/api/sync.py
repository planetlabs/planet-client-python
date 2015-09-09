# Copyright 2015 Planet Labs, Inc.
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
import itertools
import json
import logging
import os
from os import path
import threading
from ._fatomic import atomic_open
from . import exceptions
from .utils import complete
from .utils import strp_timestamp
from .utils import strf_timestamp
from .utils import write_to_file


_logger = logging.getLogger(__name__)


class _SyncTool(object):

    def __init__(self, client, destination, aoi, scene_type, products,
                 **filters):
        self.client = client
        self.destination = destination
        self.aoi = aoi
        self.scene_type = scene_type
        self.products = products
        self.filters = filters
        self.workspace = filters.get('workspace', None)
        self._init()
        self.sync_file = path.join(self.destination, 'sync.json')
        self.error_handler = _logger.exception
        self._cancel = False

    def _init(self):
        dest = self.destination
        if not path.exists(dest) or not path.isdir(dest):
            raise ValueError('destination must exist and be a directory')
        if self.aoi is None:
            aoi_file = path.join(dest, 'aoi.geojson')
            missing = not path.exists(aoi_file)
            if missing and self.workspace is None:
                raise ValueError('no aoi provided and no aoi.geojson file')
            elif not missing:
                self._read_aoi(aoi_file)

    def _read_aoi(self, aoi_file):
        with open(aoi_file) as fp:
            try:
                self.aoi = json.loads(fp.read())
            except ValueError:
                msg = '%s does not contain valid JSON' % aoi_file
                raise ValueError(msg)

    def _read_sync_file(self):
        if path.exists(self.sync_file):
            with open(self.sync_file) as fp:
                sync = json.loads(fp.read())
        else:
            sync = {}
        return sync

    def init(self, limit=-1):
        sync = self._read_sync_file()
        if 'latest' in sync:
            self.filters['published.gt'] = sync['latest']

        resp = self.client.get_scenes_list(scene_type=self.scene_type,
                                           intersects=self.aoi,
                                           count=100,
                                           order_by='acquired asc',
                                           **self.filters)
        self._scenes = resp
        count = resp.get()['count']
        self._scene_count = count if limit < 0 else limit
        return count * len(self.products)

    def get_scenes_to_sync(self):
        return self._scenes.items_iter(limit=self._scene_count)

    def sync(self, callback):
        # init with number of scenes * products
        summary = _SyncSummary(self._scene_count * len(self.products))

        all_scenes = self.get_scenes_to_sync()
        while not self._cancel:
            # bite of chunks of work to not bog down on too many queued jobs
            scenes = list(itertools.islice(all_scenes, 100))
            if not scenes:
                break
            handlers = [
                _SyncHandler(self.destination, summary, scene, callback) for
                scene in scenes
            ]
            # start all downloads asynchronously
            for h in handlers:
                h.run(self.client, self.scene_type, self.products)
            # synchronously await them and then write metadata
            complete(handlers, self._future_handler, self.client)

        if summary.latest and not self._cancel:
            sync = self._read_sync_file()
            sync['latest'] = strf_timestamp(summary.latest)
            with atomic_open(self.sync_file, 'wb') as fp:
                fp.write(json.dumps(sync, indent=2).encode('utf-8'))

        return summary

    def _future_handler(self, futures):
        for f in futures:
            try:
                f.finish()
            except exceptions.RequestCancelled:
                self._cancel = True
                break
            except:
                self.error_handler('Unexpected error')


class _SyncSummary(object):
    '''Keep track of summary state, thread safe.'''

    def __init__(self, remaining):
        self._lock = threading.Lock()
        self.remaining = remaining
        self.transferred = 0
        self.latest = None

    def transfer_complete(self, body, metadata):
        with self._lock:
            self.remaining -= 1
            self.transferred += len(body)
            recent = strp_timestamp(metadata['properties']['published'])
            self.latest = max(self.latest, recent) if self.latest else recent


class _SyncHandler(object):
    '''Handle a sync job'''

    def __init__(self, destination, summary, metadata, user_callback):
        self.destination = destination
        self.summary = summary
        self.metadata = metadata
        self.user_callback = user_callback or (lambda *args: None)
        self._cancel = False
        self.futures = []

    def run(self, client, scene_type, products):
        '''start asynchronous execution, must call finish to await'''
        if self._cancel:
            return
        for product in products:
            self.futures.extend(client.fetch_scene_geotiffs(
                                [self.metadata['id']],
                                scene_type, product,
                                callback=self))

    def cancel(self):
        '''cancel pending downloads'''
        self._cancel = True
        futures = getattr(self, 'futures', [])
        for f in futures:
            f.cancel()

    def finish(self):
        '''await pending downloads and write out metadata
        @todo this is not an atomic operation - it's possible that one
              product gets downloaded and the other fails.
        '''
        if self._cancel:
            return

        for f in self.futures:
            f.await()

        if self._cancel:
            return

        # write out metadata
        metadata = os.path.join(self.destination,
                                '%s_metadata.json' % self.metadata['id'])
        with atomic_open(metadata, 'wb') as fp:
            fp.write(json.dumps(self.metadata, indent=2).encode('utf-8'))

    def __call__(self, body):
        '''implement the callback that runs when the scene response is ready'''
        # first write scene to disk
        write_to_file(self.destination)(body)

        # summarize
        self.summary.transfer_complete(body, self.metadata)

        # invoke any callback with file completed and how many left
        self.user_callback(body.name, self.summary.remaining)
