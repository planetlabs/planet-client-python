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
"""Functionality for processing inputs and outputs."""
import logging
import typing

from . import exceptions, geojson

LOGGER = logging.getLogger(__name__)


async def collect(
    values: typing.AsyncIterator[dict]
) -> typing.Union[typing.List[dict], dict]:
    """Collect a sequence into JSON.

    If the items in values are GeoJSON features, the JSON blob is a GeoJSON
    FeatureCollection. Otherwise, the JSON blob is a list of the items.

    Returns:
        JSON blob containing all sequence entries.
    """
    as_list = [v async for v in values]

    ret: typing.Union[typing.List[dict], dict]
    try:
        ret = geojson.as_featurecollection(as_list)
    except exceptions.GeoJSONError:
        ret = as_list

    return ret
