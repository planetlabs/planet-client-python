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

from planet import exceptions
from planet.cli.options import pretty


def command(group: click.Group):
    """a decorator that adds common utilities/options to a click command

    usage:

    @command(features)  # pass a group created with @click.group
    def my_command():
        ...

    this single decorator replaces a list of decorators we would otherwise
    add to every function e.g.:

    @features.command
    @coro
    @translate_exceptions
    @click.pass_context
    def my_command():
        ...
    """

    # the decorators to add to the function **when the function is run**
    # (as opposed to when the function is registered as a click command)
    decorators = [
        translate_exceptions,
        coro,
    ]

    # click specific functionality e.g. any decorators that
    # register an extra argument for the function
    click_fns = [
        click.pass_context,
        pretty,
    ]

    # since we want to use `command` as a function with an arg: `@command(group)`,
    # we need to create and return an "real" decorator that takes the function as its
    # arg.
    def decorator(f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            cmd = f

            # wrap cmd with all the default decorators
            for d in decorators:
                cmd = d(f)

            return cmd(*args, **kwargs)

        # run any click-specific registration decorators
        for fn in click_fns:
            f = fn(f)

        # register the whole thing as a Click command.
        # Doing this last (outside the wrapper) allows click to
        # pick up the options/arguments added to the command by e.g.
        # `@click.option()`
        return group.command(wrapper)

    return decorator


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
        except exceptions.AuthException:
            raise click.ClickException(
                'Auth information does not exist or is corrupted. Initialize '
                'with `planet auth init`.')
        except exceptions.PlanetError as ex:
            raise click.ClickException(str(ex))

    return wrapper
