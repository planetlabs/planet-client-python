# Copyright 2022-2025 Planet Labs PBC.
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
import planet_auth_utils

LOGGER = logging.getLogger(__name__)


@click.group("auth")  # type: ignore
@click.pass_context
def cmd_auth(ctx):
    """
    Commands for working with Planet authentication.
    """


cmd_auth.add_command(name="login", cmd=planet_auth_utils.cmd_plauth_login)
planet_auth_utils.monkeypatch_hide_click_cmd_options(
    planet_auth_utils.cmd_plauth_login,
    [
        # Hide client ID / client secret until we are ready for OAuth M2M
        # "auth_client_id",
        # "auth_client_secret",
        # Hide audience and organization.  They are useful for plauth as a
        # generic OAuth client, but within the planet SDK we only care about
        # the built-ins.
        "audience",
        "organization",
        # Hide project.  We have not finalized or publicly released the
        # project selection interface.
        "project",
    ])

# TODO: mark print-api-key as deprecated when we better support M2M tokens
# planet_auth_utils.cmd_pllegacy_print_api_key.deprecated = True
cmd_auth.add_command(name="print-api-key",
                     cmd=planet_auth_utils.cmd_pllegacy_print_api_key)
cmd_auth.add_command(name="print-access-token",
                     cmd=planet_auth_utils.cmd_oauth_print_access_token)
cmd_auth.add_command(name="refresh", cmd=planet_auth_utils.cmd_oauth_refresh)
cmd_auth.add_command(name="reset", cmd=planet_auth_utils.cmd_plauth_reset)


# We are only plumbing a sub-set of the util lib's "profile" command,
# which is why we shadow it.
@click.group("profile")
@click.pass_context
def cmd_auth_profile(ctx):
    """
    Manage auth profiles.
    """


cmd_auth_profile.add_command(name="list",
                             cmd=planet_auth_utils.cmd_profile_list)
cmd_auth_profile.add_command(name="show",
                             cmd=planet_auth_utils.cmd_profile_show)
cmd_auth_profile.add_command(name="set", cmd=planet_auth_utils.cmd_profile_set)
cmd_auth_profile.add_command(name="copy",
                             cmd=planet_auth_utils.cmd_profile_copy)
cmd_auth.add_command(cmd_auth_profile)
