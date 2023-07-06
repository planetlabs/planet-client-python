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
"""Auth API CLI"""
import logging
import os

import click

import planet
from planet.constants import ENV_API_KEY
from .cmds import translate_exceptions

LOGGER = logging.getLogger(__name__)


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Auth API URL.')
def auth(ctx, base_url):
    """Commands for working with Planet authentication"""
    ctx.obj['BASE_URL'] = base_url


@auth.command()  # type: ignore
@click.pass_context
@translate_exceptions
@click.option(
    '--email',
    default=None,
    prompt=True,
    help=('The email address associated with your Planet credentials.'))
@click.password_option('--password',
                       confirmation_prompt=False,
                       help=('Account password. Will not be saved.'))
def init(ctx, email, password):
    """Obtain and store authentication information"""
    base_url = ctx.obj['BASE_URL']
    plauth = planet.Auth.from_login(email, password, base_url=base_url)
    plauth.store()
    click.echo('Initialized')
    if os.getenv(ENV_API_KEY):
        click.echo(f'Warning - Environment variable {ENV_API_KEY} already '
                   'exists. To update, with the new value, use the following:')
        click.echo(f'export {ENV_API_KEY}=$(planet auth value)')


@auth.command()  # type: ignore
@translate_exceptions
def value():
    """Print the stored authentication information"""
    click.echo(planet.Auth.from_file().value)


@auth.command()  # type: ignore
@translate_exceptions
@click.argument('key')
def store(key):
    """Store authentication information"""
    plauth = planet.Auth.from_key(key)
    if click.confirm('This overrides the stored value. Continue?'):
        plauth.store()
        click.echo('Updated')
        if os.getenv(ENV_API_KEY):
            click.echo(f'Warning - Environment variable {ENV_API_KEY} already '
                       'exists. To update, with the new value, use the '
                       'following:')
            click.echo(f'export {ENV_API_KEY}=$(planet auth value)')
