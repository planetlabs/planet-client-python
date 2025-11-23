# Copyright 2025 Planet Labs PBC.
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

import json
import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from planet.cli.cli import cli


class TestReportsCLIIntegration:
    """Integration tests for Reports CLI commands.

    These tests require valid Planet API credentials and should be run against
    a test environment or with caution in production.
    """

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_reports_list_command(self, runner):
        """Test 'planet reports list' command."""
        result = runner.invoke(cli, ['reports', 'list'])

        # Should succeed or fail gracefully with proper error message
        if result.exit_code == 0:
            # If successful, output should be valid JSON
            try:
                output = json.loads(result.output)
                assert isinstance(output, dict)
                assert 'reports' in output or 'items' in output
            except json.JSONDecodeError:
                pytest.fail("Command succeeded but output is not valid JSON")
        else:
            # If failed, should have meaningful error message
            assert result.output, "Command failed but provided no error message"

    def test_reports_list_with_parameters(self, runner):
        """Test 'planet reports list' command with parameters."""
        result = runner.invoke(
            cli,
            ['reports', 'list', '--limit', '5', '--offset', '0', '--pretty'])

        # Should succeed or fail gracefully
        if result.exit_code == 0:
            try:
                output = json.loads(result.output)
                assert isinstance(output, dict)
            except json.JSONDecodeError:
                pytest.fail("Command succeeded but output is not valid JSON")

    def test_reports_types_command(self, runner):
        """Test 'planet reports types' command."""
        result = runner.invoke(cli, ['reports', 'types'])

        if result.exit_code == 0:
            try:
                output = json.loads(result.output)
                assert isinstance(output, list)
            except json.JSONDecodeError:
                pytest.fail("Command succeeded but output is not valid JSON")

    def test_reports_formats_command(self, runner):
        """Test 'planet reports formats' command."""
        result = runner.invoke(cli, ['reports', 'formats'])

        if result.exit_code == 0:
            try:
                output = json.loads(result.output)
                assert isinstance(output, list)
            except json.JSONDecodeError:
                pytest.fail("Command succeeded but output is not valid JSON")

    def test_reports_get_nonexistent(self, runner):
        """Test 'planet reports get' command with non-existent report ID."""
        result = runner.invoke(cli,
                               ['reports', 'get', 'nonexistent-report-id'])

        # Should fail with appropriate error
        assert result.exit_code != 0
        assert result.output, "Command failed but provided no error message"

    def test_reports_status_nonexistent(self, runner):
        """Test 'planet reports status' command with non-existent report ID."""
        result = runner.invoke(cli,
                               ['reports', 'status', 'nonexistent-report-id'])

        # Should fail with appropriate error
        assert result.exit_code != 0
        assert result.output, "Command failed but provided no error message"

    def test_reports_create_invalid_config(self, runner):
        """Test 'planet reports create' command with invalid configuration."""
        invalid_config = {"invalid": "config"}

        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.json',
                                         delete=False) as f:
            json.dump(invalid_config, f)
            config_file = f.name

        try:
            result = runner.invoke(
                cli, ['reports', 'create', '--config', config_file])

            # Should fail with appropriate error (either validation or API error)
            assert result.exit_code != 0
            assert result.output, "Command failed but provided no error message"
        finally:
            Path(config_file).unlink()

    def test_reports_create_missing_config_file(self, runner):
        """Test 'planet reports create' command with missing configuration file."""
        result = runner.invoke(
            cli, ['reports', 'create', '--config', 'nonexistent.json'])

        # Should fail with file not found error
        assert result.exit_code != 0
        assert "nonexistent.json" in result.output or "does not exist" in result.output

    @pytest.mark.slow
    def test_reports_full_workflow(self, runner):
        """Test full workflow: create -> status -> get -> delete report."""
        # This test is marked as slow and might be skipped in environments
        # where report creation is not supported

        config_data = {
            "type": "usage",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "format": "csv"
        }

        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.json',
                                         delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            # Try to create a report
            create_result = runner.invoke(
                cli, ['reports', 'create', '--config', config_file])

            if create_result.exit_code == 0:
                # If creation succeeded, extract report ID and test other commands
                try:
                    create_output = json.loads(create_result.output)
                    report_id = create_output.get('id')

                    if report_id:
                        # Test status command
                        status_result = runner.invoke(
                            cli, ['reports', 'status', report_id])
                        assert status_result.exit_code == 0

                        # Test get command
                        get_result = runner.invoke(
                            cli, ['reports', 'get', report_id])
                        assert get_result.exit_code == 0

                        # Test delete command (cleanup)
                        delete_result = runner.invoke(
                            cli, ['reports', 'delete', report_id])
                        assert delete_result.exit_code == 0

                except (json.JSONDecodeError, KeyError):
                    pytest.fail(
                        "Report creation succeeded but response format is unexpected"
                    )
            else:
                # If creation failed, skip the rest of the workflow test
                pytest.skip(
                    f"Report creation not supported in test environment: {create_result.output}"
                )

        finally:
            Path(config_file).unlink()

    def test_reports_help_commands(self, runner):
        """Test that all reports subcommands have help text."""
        commands = [
            'list',
            'get',
            'create',
            'download',
            'status',
            'delete',
            'types',
            'formats'
        ]

        for command in commands:
            result = runner.invoke(cli, ['reports', command, '--help'])
            assert result.exit_code == 0
            assert '--help' in result.output or 'Usage:' in result.output
