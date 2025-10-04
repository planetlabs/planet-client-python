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

from typing import Any, Dict, List, Optional
from planet.clients.reports import ReportsClient
from planet.http import Session


class ReportsAPI:

    _client: ReportsClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Reports API
                base url.
        """

        self._client = ReportsClient(session, base_url)

    def list_reports(self,
                     report_type: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     limit: Optional[int] = None,
                     offset: Optional[int] = None) -> Dict:
        """
        List available reports. By default, all reports for the requesting user's org are returned.

        Args:
            report_type (str, optional): Filter by report type (e.g., 'usage', 'billing', 'downloads').
            start_date (str, optional): Filter reports from this date (ISO 8601 format).
            end_date (str, optional): Filter reports to this date (ISO 8601 format).
            limit (int, optional): Maximum number of reports to return.
            offset (int, optional): Number of reports to skip for pagination.

        Returns:
            dict: A dictionary containing the list of reports and pagination info.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.list_reports(report_type,
                                      start_date,
                                      end_date,
                                      limit,
                                      offset))

    def get_report(self, report_id: str) -> Dict:
        """
        Get a specific report by its ID.

        Args:
            report_id (str): The ID of the report to retrieve.

        Returns:
            dict: A dictionary containing the report details.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(self._client.get_report(report_id))

    def create_report(self, request: Dict[str, Any]) -> Dict:
        """
        Create a new report.

        Args:
            request (dict): Report configuration including type, date range, and other parameters.

        Returns:
            dict: A dictionary containing the created report details including report ID.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(self._client.create_report(request))

    def download_report(self, report_id: str) -> bytes:
        """
        Download the content of a completed report.

        Args:
            report_id (str): The ID of the report to download.

        Returns:
            bytes: The report content as bytes.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(self._client.download_report(report_id))

    def get_report_status(self, report_id: str) -> Dict:
        """
        Get the status of a report.

        Args:
            report_id (str): The ID of the report to check.

        Returns:
            dict: A dictionary containing the report status information.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.get_report_status(report_id))

    def delete_report(self, report_id: str) -> Dict:
        """
        Delete a report.

        Args:
            report_id (str): The ID of the report to delete.

        Returns:
            dict: A dictionary confirming the deletion.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(self._client.delete_report(report_id))

    def list_report_types(self) -> List[Dict]:
        """
        List available report types that can be generated.

        Returns:
            list: A list of available report types with their descriptions and parameters.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(self._client.list_report_types())

    def get_report_export_formats(self) -> List[Dict]:
        """
        List available export formats for reports.

        Returns:
            list: A list of supported export formats (e.g., CSV, JSON, PDF).

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        return self._client._call_sync(
            self._client.get_report_export_formats())
