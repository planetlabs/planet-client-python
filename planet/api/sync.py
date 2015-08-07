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
import os
from os import path
import threading
from .utils import write_to_file
from .utils import strp_timestamp
from .utils import strf_timestamp


class _SyncTool(object):

    def __init__(self, client, destination, aoi, scene_type, **filters):
        self.client = client
        self.destination = destination
        self.aoi = aoi
        self.scene_type = scene_type
        self.filters = filters
        self._init()
        self.sync_file = path.join(self.destination, 'sync.json')

    def _init(self):
        dest = self.destination
        if not path.exists(dest) or not path.isdir(dest):
            raise ValueError('destination must exist and be a directory')
        if self.aoi is None:
            aoi_file = path.join(dest, 'aoi.geojson')
            if not path.exists(aoi_file):
                raise ValueError('no aoi provided and no aoi.geojson file')
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
        return count

    def get_scenes_to_sync(self):
        # @todo move to response class or utility function
        pages = (page.get() for page in self._scenes.iter())
        features = itertools.chain.from_iterable(
            (p['features'] for p in pages)
        )
        return itertools.islice(features, self._scene_count)

    def sync(self, callback):
        summary = _SyncSummary(self._scene_count)

        all_scenes = self.get_scenes_to_sync()
        while True:
            # bite of chunks of work to not bog down on too many queued jobs
            scenes = list(itertools.islice(all_scenes, 100))
            if not scenes:
                break
            handlers = [
                _SyncHandler(self.destination, summary, scene, callback) for
                scene in scenes
            ]
            futures = [h.run(self.client, self.scene_type) for h in handlers]
            for f in futures:
                f.await()

        if summary.latest:
            sync = self._read_sync_file()
            sync['latest'] = strf_timestamp(summary.latest)
            with open(self.sync_file, 'wb') as fp:
                fp.write(json.dumps(sync, indent=2).encode('utf-8'))

        return summary


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
            recent = strp_timestamp(metadata['properties']['acquired'])
            self.latest = max(self.latest, recent) if self.latest else recent


class _SyncHandler(object):
    '''Handle a sync job'''

    def __init__(self, destination, summary, metadata, user_callback):
        self.destination = destination
        self.summary = summary
        self.metadata = metadata
        self.user_callback = user_callback or (lambda *args: None)

    def run(self, client, scene_type):
        return client.fetch_scene_geotiffs(
            [self.metadata['id']],
            scene_type,
            callback=self)[0]

    def __call__(self, body):
        '''implement the callback that runs when the scene response is ready'''
        # first write scene to disk
        write_to_file(self.destination)(body)

        # write out metadata
        metadata = os.path.join(self.destination,
                                '%s_metadata.json' % self.metadata['id'])
        with open(metadata, 'wb') as fp:
            fp.write(json.dumps(self.metadata, indent=2).encode('utf-8'))

        # summarize
        self.summary.transfer_complete(body, self.metadata)

        # invoke any callback with file completed and how many left
        self.user_callback(body.name, self.summary.remaining)
