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
"""Decorators for Click commands"""
import asyncio
from functools import wraps

import click

import planet_auth

from planet import exceptions


# https://github.com/pallets/click/issues/85#issuecomment-503464628
def coro(func):
    """Wrap async functions so they can be run sync with Click.

    Parameters:
        func: a Click command function or wrapper around one.

    Returns:
        wrapper function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def translate_exceptions(func):
    """Translate internal exceptions to ClickException.

    Parameters:
        func: a Click command function or wrapper around one.

    Returns:
        wrapper function

    Raises:
        ClickException
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except planet_auth.AuthException as pla_ex:
            raise click.ClickException(
                f'{pla_ex}\n'
                'Auth information does not exist or is corrupted. Initialize '
                'with `planet auth`.') # TODO/FIXME: finalize where we want to steer users now.  `planet plauth`?
        except (exceptions.PlanetError, FileNotFoundError) as ex:
            raise click.ClickException(ex)

    return wrapper
