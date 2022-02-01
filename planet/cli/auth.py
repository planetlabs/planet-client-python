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
"""Auth API CLI"""
import logging

import click

import planet
from .cmds import translate_exceptions

LOGGER = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('-u', '--base-url',
              default=None,
              help='Assign custom base Auth API URL.')
def auth(ctx, base_url):
    '''Commands for working with Planet authentication'''
    ctx.obj['BASE_URL'] = base_url


@auth.command()
@click.pass_context
@translate_exceptions
@click.option('--email', default=None, prompt=True, help=(
    'The email address associated with your Planet credentials.'
))
@click.password_option('--password', confirmation_prompt=False, help=(
    'Account password. Will not be saved.'
))
def init(ctx, email, password):
    '''Obtain and store authentication information'''
    base_url = ctx.obj["BASE_URL"]
    plauth = planet.Auth.from_login(email, password, base_url=base_url)
    plauth.write()
    click.echo('Initialized')


@auth.command()
@translate_exceptions
def value():
    '''Print the stored authentication information'''
    click.echo(planet.Auth.from_file().value)
