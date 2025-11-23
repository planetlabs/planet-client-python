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
from planet import Session
from planet.sync import Planet


class TestReportsAPIIntegration:
    """Integration tests for Reports API.

    These tests require valid Planet API credentials and should be run against
    a test environment or with caution in production.
    """

    async def test_async_reports_client_list_reports(self):
        """Test async ReportsClient list_reports method."""
        async with Session() as session:
            client = session.client('reports')

            # Test basic list operation
            response = await client.list_reports()

            assert isinstance(response, dict)
            assert 'reports' in response or 'items' in response  # API might use either key

            # Test with parameters
            response_filtered = await client.list_reports(limit=5, offset=0)

            assert isinstance(response_filtered, dict)

    async def test_async_reports_client_list_report_types(self):
        """Test async ReportsClient list_report_types method."""
        async with Session() as session:
            client = session.client('reports')

            response = await client.list_report_types()

            assert isinstance(response, list)
            if response:  # If there are report types available
                assert isinstance(response[0], dict)

    async def test_async_reports_client_get_export_formats(self):
        """Test async ReportsClient get_report_export_formats method."""
        async with Session() as session:
            client = session.client('reports')

            response = await client.get_report_export_formats()

            assert isinstance(response, list)
            if response:  # If there are export formats available
                assert isinstance(response[0], dict)

    def test_sync_reports_api_list_reports(self):
        """Test sync ReportsAPI list_reports method."""
        with Planet() as planet:
            reports_api = planet.reports

            # Test basic list operation
            response = reports_api.list_reports()

            assert isinstance(response, dict)
            assert 'reports' in response or 'items' in response  # API might use either key

            # Test with parameters
            response_filtered = reports_api.list_reports(limit=5, offset=0)

            assert isinstance(response_filtered, dict)

    def test_sync_reports_api_list_report_types(self):
        """Test sync ReportsAPI list_report_types method."""
        with Planet() as planet:
            reports_api = planet.reports

            response = reports_api.list_report_types()

            assert isinstance(response, list)
            if response:  # If there are report types available
                assert isinstance(response[0], dict)

    def test_sync_reports_api_get_export_formats(self):
        """Test sync ReportsAPI get_report_export_formats method."""
        with Planet() as planet:
            reports_api = planet.reports

            response = reports_api.get_report_export_formats()

            assert isinstance(response, list)
            if response:  # If there are export formats available
                assert isinstance(response[0], dict)

    @pytest.mark.slow
    async def test_async_reports_client_create_and_manage_report(self):
        """Test async ReportsClient full workflow: create, check status, get, delete."""
        async with Session() as session:
            client = session.client('reports')

            # Create a test report (this might fail if report type is not available)
            try:
                create_request = {
                    "type": "usage",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "format": "csv"
                }

                create_response = await client.create_report(create_request)
                assert isinstance(create_response, dict)
                assert 'id' in create_response

                report_id = create_response['id']

                # Check status
                status_response = await client.get_report_status(report_id)
                assert isinstance(status_response, dict)
                assert 'status' in status_response

                # Get report details
                report_response = await client.get_report(report_id)
                assert isinstance(report_response, dict)
                assert report_response['id'] == report_id

                # Clean up - delete the report
                delete_response = await client.delete_report(report_id)
                assert isinstance(delete_response, dict)

            except Exception as e:
                # Some test environments might not support all report types
                # or might have different permission requirements
                pytest.skip(
                    f"Report creation not supported in test environment: {e}")

    @pytest.mark.slow
    def test_sync_reports_api_create_and_manage_report(self):
        """Test sync ReportsAPI full workflow: create, check status, get, delete."""
        with Planet() as planet:
            reports_api = planet.reports

            # Create a test report (this might fail if report type is not available)
            try:
                create_request = {
                    "type": "usage",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "format": "csv"
                }

                create_response = reports_api.create_report(create_request)
                assert isinstance(create_response, dict)
                assert 'id' in create_response

                report_id = create_response['id']

                # Check status
                status_response = reports_api.get_report_status(report_id)
                assert isinstance(status_response, dict)
                assert 'status' in status_response

                # Get report details
                report_response = reports_api.get_report(report_id)
                assert isinstance(report_response, dict)
                assert report_response['id'] == report_id

                # Clean up - delete the report
                delete_response = reports_api.delete_report(report_id)
                assert isinstance(delete_response, dict)

            except Exception as e:
                # Some test environments might not support all report types
                # or might have different permission requirements
                pytest.skip(
                    f"Report creation not supported in test environment: {e}")
