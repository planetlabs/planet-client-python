# Copyright 2022 Planet Labs PBC.
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
"""Helpers for CLI I/O"""
import json

import click


def echo_json(obj: object, pretty: bool = False) -> None:
    """

    Parameters:
        obj: any object serializeable to JSON
        pretty: whether to reformat for easy visualization

    Returns:
        None
    """
    if pretty:
        json_str = json.dumps(obj, indent=2, sort_keys=True)
        click.echo(json_str)
    else:
        click.echo(json.dumps(obj))
