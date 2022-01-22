# Copyright 2022 Planet Labs, PBC.
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
"""Utilities for CLI modules"""
import asyncio
from functools import wraps
import json

import click

import planet


# https://github.com/pallets/click/issues/85#issuecomment-503464628
def coro(f):
    '''Wraps async functions so they can be run sync with Click.'''
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


def handle_exceptions(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except planet.exceptions.APIException as ex:
            raise click.ClickException(ex)
    return wrapper


def get_auth():
    try:
        auth = planet.Auth.from_file()
    except planet.auth.AuthException:
        raise click.ClickException(
            'Auth information does not exist or is corrupted. Initialize '
            'with `planet auth init`.')
    return auth


def json_echo(json_dict, pretty):
    if pretty:
        json_str = json.dumps(json_dict, indent=2, sort_keys=True)
        click.echo(json_str)
    else:
        click.echo(json.dumps(json_dict))
