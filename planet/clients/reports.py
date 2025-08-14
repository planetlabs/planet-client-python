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

import logging
from typing import Any, Dict, List, Optional, TypeVar

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError
from planet.http import Session
from ..constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/reports/v1/'

LOGGER = logging.getLogger()

T = TypeVar("T")


class ReportsClient(_BaseClient):
    """Asynchronous Reports API client.

    The Reports API allows Organization Administrators to download usage reports
    systematically for internal processing and analysis. Reports downloaded from
    the API are the exact same reports available from the user interface
    accessible from your Account at www.planet.com/account.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('reports')
        ...         # use client here
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production reports
                API base url.
        """
        super().__init__(session, base_url or BASE_URL)

    async def list_reports(self,
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
        params: Dict[str, Any] = {}
        if report_type is not None:
            params["type"] = report_type
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        try:
            response = await self._session.request(method='GET',
                                                   url=self._base_url,
                                                   params=params)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            reports_response = response.json()
            return reports_response

    async def get_report(self, report_id: str) -> Dict:
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
        url = f'{self._base_url}/{report_id}'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            report = response.json()
            return report

    async def create_report(self, request: Dict[str, Any]) -> Dict:
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
        try:
            response = await self._session.request(method='POST',
                                                   url=self._base_url,
                                                   json=request)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            report = response.json()
            return report

    async def download_report(self, report_id: str) -> bytes:
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
        url = f'{self._base_url}/{report_id}/download'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            return response.content

    async def get_report_status(self, report_id: str) -> Dict:
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
        url = f'{self._base_url}/{report_id}/status'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            status = response.json()
            return status

    async def delete_report(self, report_id: str) -> Dict:
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
        url = f'{self._base_url}/{report_id}'
        try:
            response = await self._session.request(method='DELETE', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            result = response.json()
            return result

    async def list_report_types(self) -> List[Dict]:
        """
        List available report types that can be generated.

        Returns:
            list: A list of available report types with their descriptions and parameters.

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        url = f'{self._base_url}/types'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            types = response.json()
            return types

    async def get_report_export_formats(self) -> List[Dict]:
        """
        List available export formats for reports.

        Returns:
            list: A list of supported export formats (e.g., CSV, JSON, PDF).

        Raises:
            APIError: If the API returns an error response.
            ClientError: If there is an issue with the client request.
        """
        url = f'{self._base_url}/formats'
        try:
            response = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:
            raise
        else:
            formats = response.json()
            return formats
