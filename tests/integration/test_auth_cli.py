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

import unittest

# import pytest
from click.testing import CliRunner

from planet.cli import cli


# TODO: A unit test of the auth cli really should just be checking that
#       AuthClient is called with the expected arguments.  This test right
#       now isn't that sophisticated, looking for some known side effects
#       of the 'noop' auth implementation, and looks for things completely
#       exploding.
# FIXME: it may be that I want to refactor Auth(), Credential() or the
#        auth click command a little as I work on this. Some of the
#        encapsulation is leaky.
class AuthTest(unittest.TestCase):

    @staticmethod
    def invoke_auth_cli(extra_args):
        runner = CliRunner()
        args = ['--auth-profile', 'none', 'auth'] + extra_args
        return runner.invoke(cli.main, args=args)

    def test_default_cmd(self):
        result = self.invoke_auth_cli([])
        self.assertEqual(0, result.exit_code)
        self.assertTrue('Usage:' in result.stdout)

    def test_list_scopes(self):
        result = self.invoke_auth_cli(['list-scopes'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual('[]\n', result.stdout)

    def test_login(self):
        result = self.invoke_auth_cli(['login'])
        self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_print_access_token(self):
    #     result = self.invoke_auth_cli(['print-access-token'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_print_api_key(self):
    #     result = self.invoke_auth_cli(['print-api-key'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_refresh(self):
    #     result = self.invoke_auth_cli(['refresh'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_validate_access_token(self):
    #     result = self.invoke_auth_cli(['validate-access-token'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_validate_id_token(self):
    #     result = self.invoke_auth_cli(['validate-id-token'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_validate_id_token_local(self):
    #     result = self.invoke_auth_cli(['validate-id-token-local'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_validate_refresh_token(self):
    #     result = self.invoke_auth_cli(['validate-refresh-token'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_revoke_access_token(self):
    #     result = self.invoke_auth_cli(['revoke-access-token'])
    #     self.assertEqual(0, result.exit_code)

    # @pytest.mark.skip(
    #     'Skipping test that is specific to a particular auth implementation')
    # def test_revoke_refresh_token(self):
    #     result = self.invoke_auth_cli(['revoke-refresh-token'])
    #     self.assertEqual(0, result.exit_code)
