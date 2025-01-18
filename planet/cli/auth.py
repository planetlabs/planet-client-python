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

import click

import planet_auth
import planet_auth_utils

from .cmds import translate_exceptions
from ..auth_builtins import _BuiltinConfigurationProvider

LOGGER = logging.getLogger(__name__)


@click.group()  # type: ignore
@click.pass_context
def auth(ctx):
    """Commands for working with Planet authentication"""
    # Override the default current_auth_context stored in ctx.obj["AUTH"]
    # for legacy auth sub-commands.  The planet_auth_utils library provides very
    # generic utility commands, and the click commands it provides do not know
    # about specific deployments.  This library is specifically geared
    # for the customer facing Planet Insights Platform, and provides
    # built-in configurations for the public API surface area.
    #
    # We also employ bit of hackery to maintain old behavior - point
    # FileBackedPlanetLegacyApiKey (the "Credential" or "token_file") to the
    # ~/.planet.json file nominally used by PlanetAuthUserConfig.  A common
    # base class is used to model these separate use cases, and plays well
    # with merged key sets.  planet_auth_utils uses this file for more than
    # just storing the API key, and nominally stores legacy API keys in a
    # different location(s).  This planet SDK historically only stored an
    # API key in this file.
    if (ctx.invoked_subcommand == "init" or ctx.invoked_subcommand == "value"
            or ctx.invoked_subcommand == "store"):
        # click.echo("Overriding Auth Profile with legacy auth profile.")
        ctx.obj[
            "AUTH"] = planet_auth_utils.PlanetAuthFactory.initialize_auth_client_context(
                auth_profile_opt=_BuiltinConfigurationProvider.
                BUILTIN_PROFILE_NAME_LEGACY,
                token_file_opt=planet_auth_utils.PlanetAuthUserConfig.
                default_user_config_file())


@auth.command(name="store", deprecated=True)  # type: ignore
@translate_exceptions
@click.argument('key')
def store(key):
    """Store authentication information"""
    if click.confirm('This overrides the stored value. Continue?'):
        # See above.  A bit of hackery around the token_file to maintain old interface.
        token_file = planet_auth.FileBackedJsonObject(
            file_path=planet_auth_utils.PlanetAuthUserConfig.
            default_user_config_file())
        try:
            token_file.load()
            conf_data = token_file.data()
        except FileNotFoundError:
            conf_data = {}

        conf_data["key"] = key
        token_file.set_data(conf_data)
        token_file.save()


# We implement the "planet auth" sub-command in terms of the planet_auth_utils
# click commands as much as we can.

auth.add_command(name="login", cmd=planet_auth_utils.cmd_plauth_login)
auth.add_command(name="print-access-token",
                 cmd=planet_auth_utils.cmd_oauth_print_access_token)
auth.add_command(name="profile-list", cmd=planet_auth_utils.cmd_profile_list)
auth.add_command(name="profile-show", cmd=planet_auth_utils.cmd_profile_show)
auth.add_command(name="profile-set", cmd=planet_auth_utils.cmd_profile_set)

planet_auth_utils.cmd_pllegacy_login.name = "init"
planet_auth_utils.cmd_pllegacy_login.deprecated = True
auth.add_command(name="init", cmd=planet_auth_utils.cmd_pllegacy_login)

planet_auth_utils.cmd_pllegacy_print_api_key.name = "value"
planet_auth_utils.cmd_pllegacy_print_api_key.deprecated = True
auth.add_command(name="value",
                 cmd=planet_auth_utils.cmd_pllegacy_print_api_key)
