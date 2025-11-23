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

import pytest
from unittest.mock import Mock, patch
from planet.sync.reports import ReportsAPI


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def reports_api(mock_session):
    return ReportsAPI(mock_session)


class TestReportsAPI:

    @patch('planet.sync.reports.ReportsClient')
    def test_init(self, mock_reports_client, mock_session):
        ReportsAPI(mock_session)
        mock_reports_client.assert_called_once_with(mock_session, None)

    @patch('planet.sync.reports.ReportsClient')
    def test_init_with_base_url(self, mock_reports_client, mock_session):
        custom_url = 'https://custom.api.com/reports/v1/'
        ReportsAPI(mock_session, custom_url)
        mock_reports_client.assert_called_once_with(mock_session, custom_url)

    def test_list_reports(self, reports_api):
        expected_result = {"reports": [], "total": 0}
        reports_api._client.list_reports.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.list_reports(report_type="usage",
                                          start_date="2024-01-01",
                                          end_date="2024-01-31",
                                          limit=10,
                                          offset=0)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_get_report(self, reports_api):
        report_id = "report123"
        expected_result = {"id": report_id, "type": "usage"}
        reports_api._client.get_report.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.get_report(report_id)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_create_report(self, reports_api):
        request_data = {"type": "usage", "start_date": "2024-01-01"}
        expected_result = {"id": "report123", "status": "pending"}
        reports_api._client.create_report.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.create_report(request_data)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_download_report(self, reports_api):
        report_id = "report123"
        expected_result = b"report,data\nvalue1,value2\n"
        reports_api._client.download_report.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.download_report(report_id)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_get_report_status(self, reports_api):
        report_id = "report123"
        expected_result = {"id": report_id, "status": "processing"}
        reports_api._client.get_report_status.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.get_report_status(report_id)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_delete_report(self, reports_api):
        report_id = "report123"
        expected_result = {"message": "Report deleted successfully"}
        reports_api._client.delete_report.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.delete_report(report_id)

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_list_report_types(self, reports_api):
        expected_result = [{"type": "usage"}, {"type": "billing"}]
        reports_api._client.list_report_types.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.list_report_types()

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result

    def test_get_report_export_formats(self, reports_api):
        expected_result = [{"format": "csv"}, {"format": "json"}]
        reports_api._client.get_report_export_formats.return_value = "async_coroutine"
        reports_api._client._call_sync.return_value = expected_result

        result = reports_api.get_report_export_formats()

        reports_api._client._call_sync.assert_called_once_with(
            "async_coroutine")
        assert result == expected_result
