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

# results are 'future' objects and we have to ensure they all process
map(lambda r: r.result(), results)
