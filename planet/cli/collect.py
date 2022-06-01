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
"""Functionality for collecting a sequence into JSON."""
import json
import logging

import click

import planet
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import pretty

LOGGER = logging.getLogger(__name__)


@click.command()
@click.pass_context
@translate_exceptions
@coro
@click.argument('input', type=click.File('r'))
@pretty
async def collect(ctx, input, pretty):
    """Collect a sequence of JSON descriptions into a single JSON blob.

    If the descriptions represent GeoJSON features, a GeoJSON FeatureCollection
    is returned.

    Output can be pretty-printed with --pretty option.
    """

    # make an AsyncGenerator from the input lines
    async def _entries_aiter():
        for line in input:
            yield json.loads(line)

    entries = _entries_aiter()
    collected = await planet.collect(entries)
    echo_json(collected, pretty)
