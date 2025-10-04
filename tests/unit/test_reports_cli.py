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
from unittest.mock import AsyncMock, Mock, patch
from click.testing import CliRunner

from planet.cli.reports import (reports,
                                list_reports_cmd,
                                get_report_cmd,
                                create_report_cmd,
                                download_report_cmd,
                                get_report_status_cmd,
                                delete_report_cmd,
                                list_report_types_cmd,
                                get_report_export_formats_cmd)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_ctx():
    ctx = Mock()
    ctx.obj = {'BASE_URL': None}
    return ctx


class TestReportsCLI:

    def test_reports_group_default_base_url(self, runner):
        result = runner.invoke(reports, ['--help'])
        assert result.exit_code == 0
        assert 'Commands for interacting with the Reports API' in result.output

    def test_reports_group_custom_base_url(self, runner):
        custom_url = 'https://custom.api.com/reports/v1/'
        result = runner.invoke(reports, ['-u', custom_url, '--help'])
        assert result.exit_code == 0

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_list_reports_cmd_no_params(self,
                                        mock_echo_json,
                                        mock_reports_client,
                                        runner,
                                        mock_ctx):
        mock_client = AsyncMock()
        mock_client.list_reports.return_value = {"reports": [], "total": 0}
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(list_reports_cmd, [], obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.list_reports.assert_called_once_with(report_type=None,
                                                         start_date=None,
                                                         end_date=None,
                                                         limit=None,
                                                         offset=None)

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_list_reports_cmd_with_params(self,
                                          mock_echo_json,
                                          mock_reports_client,
                                          runner,
                                          mock_ctx):
        mock_client = AsyncMock()
        mock_client.list_reports.return_value = {
            "reports": [{
                "id": "report1"
            }], "total": 1
        }
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(list_reports_cmd,
                               [
                                   '--type',
                                   'usage',
                                   '--start-date',
                                   '2024-01-01',
                                   '--end-date',
                                   '2024-01-31',
                                   '--limit',
                                   '10',
                                   '--offset',
                                   '0',
                                   '--pretty'
                               ],
                               obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.list_reports.assert_called_once_with(
            report_type='usage',
            start_date='2024-01-01',
            end_date='2024-01-31',
            limit=10,
            offset=0)

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_get_report_cmd(self,
                            mock_echo_json,
                            mock_reports_client,
                            runner,
                            mock_ctx):
        mock_client = AsyncMock()
        mock_client.get_report.return_value = {
            "id": "report123", "type": "usage"
        }
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(get_report_cmd, ['report123'], obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.get_report.assert_called_once_with('report123')

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_create_report_cmd(self,
                               mock_echo_json,
                               mock_reports_client,
                               runner,
                               mock_ctx):
        mock_client = AsyncMock()
        mock_client.create_report.return_value = {
            "id": "report123", "status": "pending"
        }
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        config_data = {
            "type": "usage",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }

        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.json',
                                         delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            result = runner.invoke(create_report_cmd,
                                   ['--config', config_file],
                                   obj=mock_ctx.obj)
            assert result.exit_code == 0
            mock_client.create_report.assert_called_once_with(config_data)
        finally:
            Path(config_file).unlink()

    def test_create_report_cmd_missing_config(self, runner, mock_ctx):
        result = runner.invoke(create_report_cmd, [], obj=mock_ctx.obj)
        assert result.exit_code != 0
        assert 'Missing option "--config"' in result.output

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.click.echo')
    def test_download_report_cmd_to_file(self,
                                         mock_echo,
                                         mock_reports_client,
                                         runner,
                                         mock_ctx):
        mock_client = AsyncMock()
        mock_client.download_report.return_value = b"report,data\nvalue1,value2\n"
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            result = runner.invoke(download_report_cmd,
                                   ['report123', '--output', output_file],
                                   obj=mock_ctx.obj)

            assert result.exit_code == 0
            mock_client.download_report.assert_called_once_with('report123')

            # Verify file was written
            content = Path(output_file).read_bytes()
            assert content == b"report,data\nvalue1,value2\n"
        finally:
            Path(output_file).unlink()

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.click.echo')
    def test_download_report_cmd_to_stdout(self,
                                           mock_echo,
                                           mock_reports_client,
                                           runner,
                                           mock_ctx):
        mock_client = AsyncMock()
        mock_client.download_report.return_value = b"report,data\nvalue1,value2\n"
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(download_report_cmd, ['report123'],
                               obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.download_report.assert_called_once_with('report123')
        mock_echo.assert_called_with("report,data\nvalue1,value2\n")

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_get_report_status_cmd(self,
                                   mock_echo_json,
                                   mock_reports_client,
                                   runner,
                                   mock_ctx):
        mock_client = AsyncMock()
        mock_client.get_report_status.return_value = {
            "id": "report123", "status": "processing"
        }
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(get_report_status_cmd, ['report123'],
                               obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.get_report_status.assert_called_once_with('report123')

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_delete_report_cmd(self,
                               mock_echo_json,
                               mock_reports_client,
                               runner,
                               mock_ctx):
        mock_client = AsyncMock()
        mock_client.delete_report.return_value = {
            "message": "Report deleted successfully"
        }
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(delete_report_cmd, ['report123'],
                               obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.delete_report.assert_called_once_with('report123')

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_list_report_types_cmd(self,
                                   mock_echo_json,
                                   mock_reports_client,
                                   runner,
                                   mock_ctx):
        mock_client = AsyncMock()
        mock_client.list_report_types.return_value = [{
            "type": "usage"
        }, {
            "type": "billing"
        }]
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(list_report_types_cmd, [], obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.list_report_types.assert_called_once()

    @patch('planet.cli.reports.reports_client')
    @patch('planet.cli.reports.echo_json')
    def test_get_report_export_formats_cmd(self,
                                           mock_echo_json,
                                           mock_reports_client,
                                           runner,
                                           mock_ctx):
        mock_client = AsyncMock()
        mock_client.get_report_export_formats.return_value = [{
            "format": "csv"
        }, {
            "format": "json"
        }]
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(get_report_export_formats_cmd, [],
                               obj=mock_ctx.obj)

        assert result.exit_code == 0
        mock_client.get_report_export_formats.assert_called_once()

    @patch('planet.cli.reports.reports_client')
    def test_error_handling(self, mock_reports_client, runner, mock_ctx):
        mock_client = AsyncMock()
        mock_client.list_reports.side_effect = Exception("API Error")
        mock_reports_client.return_value.__aenter__.return_value = mock_client

        result = runner.invoke(list_reports_cmd, [], obj=mock_ctx.obj)

        assert result.exit_code != 0
        assert "Failed to list reports: API Error" in result.output
