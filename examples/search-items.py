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

from planet import api
from planet.api import filters
from sys import stdout

# cloudy by date - a silly example to see when it is cloudiest according
# to planet imagery
#
# output a CSV of PlanetScope item-id, cloud cover, and date acquired
# for a region around the San Fransisco peninsula

# geojson AOI
aoi = {
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
}

# will pick up api_key via environment variable PL_API_KEY
# but can be specified using `api_key` named argument
client = api.ClientV1()

# build a query using the AOI and
# a cloud_cover filter that excludes 'cloud free' scenes
query = filters.and_filter(
    filters.geom_filter(aoi),
    filters.range_filter('cloud_cover', gt=0),
)

# build a request for only PlanetScope imagery
request = filters.build_search_request(
    query, item_types=['PSScene3Band', 'PSScene4Band']
)

# if you don't have an API key configured, this will raise an exception
result = client.quick_search(request)

stdout.write('id,cloud_cover,date\n')

# items_iter returns a limited iterator of all results. behind the scenes,
# the client is paging responses from the API
for item in result.items_iter(limit=None):
    props = item['properties']
    stdout.write('{0},{cloud_cover},{acquired}\n'.format(item['id'], **props))
