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
from unittest.mock import AsyncMock, Mock
from planet.clients.reports import ReportsClient
from planet.exceptions import APIError, ClientError


@pytest.fixture
def mock_session():
    session = Mock()
    session.request = AsyncMock()
    return session


@pytest.fixture
def reports_client(mock_session):
    return ReportsClient(mock_session)


class TestReportsClient:

    async def test_list_reports_no_params(self, reports_client, mock_session):
        expected_response = {
            "reports": [], "total": 0, "limit": 50, "offset": 0
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.list_reports()

        mock_session.request.assert_called_once_with(
            method='GET', url='https://api.planet.com/reports/v1/', params={})
        assert result == expected_response

    async def test_list_reports_with_params(self, reports_client,
                                            mock_session):
        expected_response = {
            "reports": [{
                "id": "report1", "type": "usage"
            }],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.list_reports(report_type="usage",
                                                   start_date="2024-01-01",
                                                   end_date="2024-01-31",
                                                   limit=10,
                                                   offset=0)

        mock_session.request.assert_called_once_with(
            method='GET',
            url='https://api.planet.com/reports/v1/',
            params={
                "type": "usage",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "limit": 10,
                "offset": 0
            })
        assert result == expected_response

    async def test_get_report(self, reports_client, mock_session):
        report_id = "report123"
        expected_response = {
            "id": report_id,
            "type": "usage",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.get_report(report_id)

        mock_session.request.assert_called_once_with(
            method='GET', url=f'https://api.planet.com/reports/v1/{report_id}')
        assert result == expected_response

    async def test_create_report(self, reports_client, mock_session):
        request_data = {
            "type": "usage",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "format": "csv"
        }
        expected_response = {
            "id": "report123",
            "type": "usage",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.create_report(request_data)

        mock_session.request.assert_called_once_with(
            method='POST',
            url='https://api.planet.com/reports/v1/',
            json=request_data)
        assert result == expected_response

    async def test_download_report(self, reports_client, mock_session):
        report_id = "report123"
        expected_content = b"report,data\nvalue1,value2\n"
        mock_response = Mock()
        mock_response.content = expected_content
        mock_session.request.return_value = mock_response

        result = await reports_client.download_report(report_id)

        mock_session.request.assert_called_once_with(
            method='GET',
            url=f'https://api.planet.com/reports/v1/{report_id}/download')
        assert result == expected_content

    async def test_get_report_status(self, reports_client, mock_session):
        report_id = "report123"
        expected_response = {
            "id": report_id, "status": "processing", "progress": 50
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.get_report_status(report_id)

        mock_session.request.assert_called_once_with(
            method='GET',
            url=f'https://api.planet.com/reports/v1/{report_id}/status')
        assert result == expected_response

    async def test_delete_report(self, reports_client, mock_session):
        report_id = "report123"
        expected_response = {"message": "Report deleted successfully"}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.delete_report(report_id)

        mock_session.request.assert_called_once_with(
            method='DELETE',
            url=f'https://api.planet.com/reports/v1/{report_id}')
        assert result == expected_response

    async def test_list_report_types(self, reports_client, mock_session):
        expected_response = [{
            "type": "usage", "description": "Usage report"
        },
                             {
                                 "type": "billing",
                                 "description": "Billing report"
                             }]
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.list_report_types()

        mock_session.request.assert_called_once_with(
            method='GET', url='https://api.planet.com/reports/v1/types')
        assert result == expected_response

    async def test_get_report_export_formats(self,
                                             reports_client,
                                             mock_session):
        expected_response = [{
            "format": "csv", "description": "Comma-separated values"
        },
                             {
                                 "format": "json",
                                 "description": "JavaScript Object Notation"
                             }]
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_session.request.return_value = mock_response

        result = await reports_client.get_report_export_formats()

        mock_session.request.assert_called_once_with(
            method='GET', url='https://api.planet.com/reports/v1/formats')
        assert result == expected_response

    async def test_api_error_handling(self, reports_client, mock_session):
        mock_session.request.side_effect = APIError("API Error")

        with pytest.raises(APIError):
            await reports_client.list_reports()

    async def test_client_error_handling(self, reports_client, mock_session):
        mock_session.request.side_effect = ClientError("Client Error")

        with pytest.raises(ClientError):
            await reports_client.get_report("report123")

    def test_init_default_base_url(self, mock_session):
        client = ReportsClient(mock_session)
        assert client._base_url == 'https://api.planet.com/reports/v1'

    def test_init_custom_base_url(self, mock_session):
        custom_url = 'https://custom.api.com/reports/v1/'
        client = ReportsClient(mock_session, custom_url)
        assert client._base_url == 'https://custom.api.com/reports/v1'
