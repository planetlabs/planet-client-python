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
import warnings
import click

from planet_auth import Auth as PLAuth
from planet_auth import PlanetLegacyAuthClientConfig as PLAuth_PlanetLegacyAuthClientConfig
from planet_auth import FileBackedPlanetLegacyApiKey as PLAuth_FileBackedPlanetLegacyApiKey
from planet_auth_config import Production as PLAuthConf_Production
import planet_auth_utils.commands.cli.planet_legacy_auth_cmd

from planet.constants import ENV_API_KEY, SECRET_FILE_PATH
from .cmds import translate_exceptions

LOGGER = logging.getLogger(__name__)


def _api_key_env_warning():
    if os.getenv(ENV_API_KEY):
        click.echo(f'Warning - Environment variable {ENV_API_KEY} already '
                   'exists. To update, with the new value, use the '
                   'following:')
        click.echo(f'export {ENV_API_KEY}=$(planet auth value)')


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Auth API URL.')
def auth(ctx, base_url):
    """Commands for working with Planet authentication"""
    # TODO: should we deprecate this whole command in favor of the functionality of the embedded 'plauth'?
    # warnings.warn("'auth' command will be deprecated.  Please use 'plauth' to manage user credentials.", PendingDeprecationWarning)

    # Override any newer style planet_auth library auth profiles and
    # always wire up the legacy auth implementation to the planet library's
    # preferred paths.
    _plauth_config = {
        **PLAuthConf_Production.LEGACY_AUTH_AUTHORITY,
        "client_type": PLAuth_PlanetLegacyAuthClientConfig.meta().get("client_type"),
    }
    if base_url:
        _plauth_config["legacy_auth_endpoint"] = base_url
    ctx.obj["AUTH"] = PLAuth.initialize_from_config_dict(client_config=_plauth_config, token_file=SECRET_FILE_PATH)


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
    ctx.invoke(planet_auth_utils.commands.cli.planet_legacy_auth_cmd.pllegacy_do_login, username=email, password=password)
    click.echo('Initialized')
    _api_key_env_warning()

@auth.command()  # type: ignore
@click.pass_context
@translate_exceptions
def value(ctx):
    """Print the stored authentication information"""
    ctx.forward(planet_auth_utils.commands.cli.planet_legacy_auth_cmd.do_print_api_key)


@auth.command()  # type: ignore
@click.pass_context
@translate_exceptions
@click.argument('key')
def store(ctx, key):
    """Store authentication information"""
    _token_file = PLAuth_FileBackedPlanetLegacyApiKey(api_key=key, api_key_file=ctx.obj["AUTH"].token_file_path())
    if click.confirm('This overrides the stored value. Continue?'):
        _token_file.save()
        click.echo('Updated')
        _api_key_env_warning()
