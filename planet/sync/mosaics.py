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

from typing import Iterator, Optional, TypeVar, Union
from planet.clients.mosaics import BBox, MosaicsClient
from planet.http import Session
from planet.models import GeoInterface, Mosaic, Quad, Series

T = TypeVar("T")


class MosaicsAPI:

    _client: MosaicsClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Mosaics API
                base url.
        """
        self._client = MosaicsClient(session, base_url)

    def get_mosaic(self, name_or_id: str) -> Mosaic:
        """Get the API representation of a mosaic by name or id.

        Parameters:
            name_or_id: The name or id of the mosaic
        """
        return self._client._call_sync(self._client.get_mosaic(name_or_id))

    def get_series(self, name_or_id: str) -> Series:
        """Get the API representation of a series by name or id.

        Parameters:
            name_or_id: The name or id of the mosaic
        """
        return self._client._call_sync(self._client.get_series(name_or_id))

    def list_series(self,
                    *,
                    name_contains: Optional[str] = None,
                    interval: Optional[str] = None,
                    acquired_gt: Optional[str] = None,
                    acquired_lt: Optional[str] = None) -> Iterator[Series]:
        """
        List the series you have access to.

        Example:

        ```python
        series = client.list_series()
        for s in series:
            print(s)
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_series(name_contains=name_contains,
                                     interval=interval,
                                     acquired_gt=acquired_gt,
                                     acquired_lt=acquired_lt))

    def list_mosaics(
        self,
        *,
        name_contains: Optional[str] = None,
        interval: Optional[str] = None,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
    ) -> Iterator[Mosaic]:
        """
        List the mosaics you have access to.

        Example:

        ```python
        mosaics = client.list_mosaics()
        for m in mosaics:
            print(m)
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_mosaics(
                name_contains=name_contains,
                interval=interval,
                acquired_gt=acquired_gt,
                acquired_lt=acquired_lt,
            ))

    def list_series_mosaics(
        self,
        /,
        series: Union[Series, str],
        *,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
        latest: bool = False,
    ) -> Iterator[Mosaic]:
        """
        List the mosaics in a series.

        Example:

        ```python
        mosaics = client.list_series_mosaics("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        for m in mosaics:
            print(m)
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_series_mosaics(
                series,
                acquired_gt=acquired_gt,
                acquired_lt=acquired_lt,
                latest=latest,
            ))

    def summarize_quads(
            self,
            /,
            mosaic: Union[Mosaic, str],
            *,
            bbox: Optional[BBox] = None,
            geometry: Optional[Union[dict, GeoInterface]] = None) -> dict:
        """
        Get a summary of a quad list for a mosaic.

        If the bbox or geometry is not provided, the entire list is considered.

        Examples:

        Get the total number of quads in the mosaic.

        ```python
        mosaic = client.get_mosaic("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        summary = client.summarize_quads(mosaic)
        print(summary["total_quads"])
        ```
        """
        return self._client._call_sync(
            self._client.summarize_quads(mosaic, bbox=bbox, geometry=geometry))

    def list_quads(
        self,
        /,
        mosaic: Union[Mosaic, str],
        *,
        minimal: bool = False,
        full_extent: bool = False,
        bbox: Optional[BBox] = None,
        geometry: Optional[Union[dict,
                                 GeoInterface]] = None) -> Iterator[Quad]:
        """
        List the a mosaic's quads.


        Parameters:
            mosaic: the mosaic to list
            minimal: if False, response includes full metadata
            full_extent: if True, the mosaic's extent will be used to list
            bbox: only quads intersecting the bbox will be listed
            geometry: only quads intersecting the geometry will be listed

        Raises:
            ValueError: if `geometry`, `bbox` or `full_extent` is not specified.

        Example:

        ```python
        mosaic = client.get_mosaic("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        quads = client.list_quads(mosaic)
        for q in quads:
            print(q)
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_quads(
                mosaic,
                minimal=minimal,
                full_extent=full_extent,
                bbox=bbox,
                geometry=geometry,
            ))

    def get_quad(self, mosaic: Union[Mosaic, str], quad_id: str) -> Quad:
        """
        Get a mosaic's quad information.

        Example:

        ```python
        quad = client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        print(quad)
        ```
        """
        return self._client._call_sync(self._client.get_quad(mosaic, quad_id))

    def get_quad_contributions(self, quad: Quad) -> list[dict]:
        """
        Get a mosaic's quad information.

        Example:

        ```python
        quad = client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        contributions = client.get_quad_contributions(quad)
        print(contributions)
        ```
        """
        return self._client._call_sync(
            self._client.get_quad_contributions(quad))

    def download_quad(self,
                      /,
                      quad: Quad,
                      *,
                      directory: str = ".",
                      overwrite: bool = False,
                      progress_bar: bool = False):
        """
        Download a quad to a directory.

        Example:

        ```python
        quad = client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        client.download_quad(quad)
        ```
        """
        self._client._call_sync(
            self._client.download_quad(quad,
                                       directory=directory,
                                       overwrite=overwrite,
                                       progress_bar=progress_bar))

    def download_quads(self,
                       /,
                       mosaic: Union[Mosaic, str],
                       *,
                       directory: Optional[str] = None,
                       overwrite: bool = False,
                       bbox: Optional[BBox] = None,
                       geometry: Optional[Union[dict, GeoInterface]] = None,
                       progress_bar: bool = False,
                       concurrency: int = 4):
        """
        Download a mosaics' quads to a directory.

        Example:

        ```python
        mosaic = cl.get_mosaic(name)
        client.download_quads(mosaic, bbox=(-100, 40, -100, 41))
        ```
        """
        return self._client._call_sync(
            self._client.download_quads(
                mosaic,
                directory=directory,
                overwrite=overwrite,
                bbox=bbox,
                geometry=geometry,
                progress_bar=progress_bar,
                concurrency=concurrency,
            ))
