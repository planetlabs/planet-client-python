# Copyright 2022 Planet Labs, PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""CLI Parameter validation"""
from typing import Optional
from planet import geojson


def check_geom(ctx, param, geometry) -> Optional[dict]:
    """Validates geometry as GeoJSON or feature ref(s)."""
    if isinstance(geometry, dict):
        return geojson.as_geom_or_ref(geometry)
    geoms = {}
    if geometry:
        for geom in geometry:
            geoms.update(geojson.as_geom_or_ref(geom))
    return geoms if geoms else None
