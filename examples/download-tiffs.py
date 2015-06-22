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

import os.path
from planet import api
import os
import sys
import tempfile

args = sys.argv[1:]
if not args:
    dest_dir = tempfile.mkdtemp(prefix='plapi')
else:
    dest_dir = args.pop()
dest_dir = os.path.abspath(dest_dir)
print 'downloading to %s' % dest_dir

# geojson AOI, WKT also supported
aoi = """{
  "type": "Polygon",
  "coordinates": [
    [
      [-122.54, 37.81],
      [-122.38, 37.84],
      [-122.35, 37.71],
      [-122.53, 37.70],
      [-122.54, 37.81]
    ]
  ]
}"""

# will pick up api_key via environment variable PL_API_KEY
# but can be specified using `api_key` named argument
client = api.Client()

# collect all scenes here
scenes = []

print 'loading scenes'

# get `count` number of scenes, for this example, use 1 to verify paging
scene = client.get_scenes_list(count=1)
# we'll use 3 `pages` of results
for s in scene.iter(pages=3):
    scenes.extend(s.get()['features'])

assert len(scenes) == 3

ids = [f['id'] for f in scenes]
print 'fetching tiffs for'
print '\n'.join(ids)
results = client.fetch_scene_thumbnails(ids, callback=api.write_to_file(dest_dir))

# results are async objects and we have to ensure they all process
map(lambda r: r.await(), results)
