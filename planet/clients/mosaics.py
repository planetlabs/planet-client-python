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

import asyncio
from pathlib import Path
from typing import AsyncIterator, Optional, Sequence, Type, TypeVar, Union, cast
from planet.clients.base import _BaseClient
from planet.constants import PLANET_BASE_URL
from planet.exceptions import ClientError, MissingResource
from planet.http import Session
from planet.models import GeoInterface, Mosaic, Paged, Quad, Response, Series, StreamingBody
from uuid import UUID

BASE_URL = f'{PLANET_BASE_URL}/basemaps/v1'

T = TypeVar("T")

Number = Union[int, float]

BBox = Sequence[Number]
"""BBox is a rectangular area described by 2 corners
where the positional meaning in the sequence is
left, bottom, right, and top, respectively
"""


class _SeriesPage(Paged):
    ITEMS_KEY = 'series'
    NEXT_KEY = '_next'


class _MosaicsPage(Paged):
    ITEMS_KEY = 'mosaics'
    NEXT_KEY = '_next'


class _QuadsPage(Paged):
    ITEMS_KEY = 'items'
    NEXT_KEY = '_next'


def _is_uuid(val: str) -> bool:
    try:
        UUID(val)
        return True
    except ValueError:
        return False


class MosaicsClient(_BaseClient):
    """High-level asynchronous access to Planet's Mosaics API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('mosaics')
        ...         # use client here
        ...
        >>> asyncio.run(main())
        ```
    """

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Mosaics
                base url.
        """
        super().__init__(session, base_url or BASE_URL)

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path}"

    async def _get_by_name(self, path: str, pager: Type[Paged],
                           name: str) -> dict:
        response = await self._session.request(
            method='GET',
            url=self._url(path),
            params={
                "name__is": name,
            },
        )
        listing = response.json()[pager.ITEMS_KEY]
        if len(listing):
            return listing[0]
        # mimic the response for 404 when search is empty
        resource = "Mosaic"
        if path == "series":
            resource = "Series"
        raise MissingResource('{"message":"%s Not Found: %s"}' %
                              (resource, name))

    async def _get_by_id(self, path: str, id: str) -> dict:
        response = await self._session.request(method="GET",
                                               url=self._url(f"{path}/{id}"))
        return response.json()

    async def _get(self, name_or_id: str, path: str,
                   pager: Type[Paged]) -> dict:
        if _is_uuid(name_or_id):
            return await self._get_by_id(path, name_or_id)
        return await self._get_by_name(path, pager, name_or_id)

    async def _resolve_mosaic(self, mosaic: Union[Mosaic, str]) -> Mosaic:
        if isinstance(mosaic, Mosaic):
            return mosaic
        return await self.get_mosaic(mosaic)

    async def get_mosaic(self, name_or_id: str) -> Mosaic:
        """Get the API representation of a mosaic by name or id.

        Parameters:
            name_or_id: The name or id of the mosaic
        """
        return Mosaic(await self._get(name_or_id, "mosaics", _MosaicsPage))

    async def get_series(self, name_or_id: str) -> Series:
        """Get the API representation of a series by name or id.

        Parameters:
            name_or_id: The name or id of the mosaic
        """
        return Series(await self._get(name_or_id, "series", _SeriesPage))

    async def list_series(
            self,
            *,
            name_contains: Optional[str] = None,
            interval: Optional[str] = None,
            acquired_gt: Optional[str] = None,
            acquired_lt: Optional[str] = None) -> AsyncIterator[Series]:
        """
        List the series you have access to.

        Example:

        ```python
        series = await client.list_series()
        async for s in series:
            print(s)
        ```
        """
        params = {}
        if name_contains:
            params["name__contains"] = name_contains
        if interval:
            params["interval"] = interval
        if acquired_gt:
            params["acquired__gt"] = acquired_gt
        if acquired_lt:
            params["acquired__lt"] = acquired_lt
        resp = await self._session.request(
            method='GET',
            url=self._url("series"),
            params=params,
        )
        async for item in _SeriesPage(resp, self._session.request):
            yield Series(item)

    async def list_mosaics(
        self,
        *,
        name_contains: Optional[str] = None,
        interval: Optional[str] = None,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
    ) -> AsyncIterator[Mosaic]:
        """
        List the mosaics you have access to.

        Example:

        ```python
        mosaics = await client.list_mosaics()
        async for m in mosaics:
            print(m)
        ```
        """
        params = {}
        if name_contains:
            params["name__contains"] = name_contains
        if interval:
            params["interval"] = interval
        if acquired_gt:
            params["acquired__gt"] = acquired_gt
        if acquired_lt:
            params["acquired__lt"] = acquired_lt
        resp = await self._session.request(
            method='GET',
            url=self._url("mosaics"),
            params=params,
        )
        async for item in _MosaicsPage(resp, self._session.request):
            yield Mosaic(item)

    async def list_series_mosaics(
        self,
        /,
        series: Union[Series, str],
        *,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
        latest: bool = False,
    ) -> AsyncIterator[Mosaic]:
        """
        List the mosaics in a series.

        Example:

        ```python
        mosaics = await client.list_series_mosaics("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        async for m in mosaics:
            print(m)
        ```
        """
        series_id = series
        if isinstance(series, Series):
            series_id = series["id"]
        elif not _is_uuid(series):
            series = Series(await self._get_by_name("series",
                                                    _SeriesPage,
                                                    series))
            series_id = series["id"]
        params = {}
        if acquired_gt:
            params["acquired__gt"] = acquired_gt
        if acquired_lt:
            params["acquired__lt"] = acquired_lt
        if latest:
            params["latest"] = "yes"
        resp = await self._session.request(
            method="GET",
            url=self._url(f"series/{series_id}/mosaics"),
            params=params,
        )
        async for item in _MosaicsPage(resp, self._session.request):
            yield Mosaic(item)

    async def summarize_quads(
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
        mosaic = await client.get_mosaic("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        summary = await client.summarize_quads(mosaic)
        print(summary["total_quads"])
        ```
        """
        resp = await self._list_quads(mosaic,
                                      minimal=True,
                                      bbox=bbox,
                                      geometry=geometry,
                                      summary=True)
        return resp.json()["summary"]

    async def list_quads(
        self,
        /,
        mosaic: Union[Mosaic, str],
        *,
        minimal: bool = False,
        full_extent: bool = False,
        bbox: Optional[BBox] = None,
        geometry: Optional[Union[dict, GeoInterface]] = None
    ) -> AsyncIterator[Quad]:
        """
        List the a mosaic's quads.

        Parameters:
            mosaic: the mosaic to list
            minimal: if False, response includes full metadata
            full_extent: if True, the mosaic's extent will be used to list
            bbox: only quads intersecting the bbox will be listed
            geometry: only quads intersecting the geometry will be listed

        Raises:
            ClientError: if `geometry`, `bbox` or `full_extent` is not specified.

        Example:

        List the quad at a single point (note the extent has the same corners)

        ```python
        mosaic = await client.get_mosaic("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        quads = await client.list_quads(mosaic, bbox=[-100, 40, -100, 40])
        async for q in quads:
            print(q)
        ```
        """
        if not any((geometry, bbox, full_extent)):
            raise ClientError("one of: geometry, bbox, full_extent required")
        resp = await self._list_quads(mosaic,
                                      minimal=minimal,
                                      bbox=bbox,
                                      geometry=geometry)
        async for item in _QuadsPage(resp, self._session.request):
            yield Quad(item)

    async def _list_quads(self,
                          /,
                          mosaic: Union[Mosaic, str],
                          *,
                          minimal: bool = False,
                          bbox: Optional[BBox] = None,
                          geometry: Optional[Union[dict, GeoInterface]] = None,
                          summary: bool = False) -> Response:
        mosaic = await self._resolve_mosaic(mosaic)
        if geometry:
            if isinstance(geometry, GeoInterface):
                geometry = geometry.__geo_interface__
            resp = await self._quads_geometry(mosaic,
                                              geometry,
                                              minimal,
                                              summary)
        else:
            if not bbox:
                xmin, ymin, xmax, ymax = cast(BBox, mosaic['bbox'])
                bbox = [
                    max(-180, xmin),
                    max(-85, ymin),
                    min(180, xmax),
                    min(85, ymax)
                ]
            resp = await self._quads_bbox(mosaic, bbox, minimal, summary)
        return resp

    async def _quads_geometry(self,
                              mosaic: Mosaic,
                              geometry: dict,
                              minimal: bool,
                              summary: bool) -> Response:
        params = {}
        if minimal:
            params["minimal"] = "true"
        if summary:
            params["summary"] = "true"
            # this could be fixed in the API ...
            # for a summary, we don't need to get any listings
            # zero is ignored, but in case that gets rejected, just use 1
            params["_page_size"] = "1"
        mosaic_id = mosaic["id"]
        return await self._session.request(
            method="POST",
            url=self._url(f"mosaics/{mosaic_id}/quads/search"),
            params=params,
            json=geometry,
        )

    async def _quads_bbox(self,
                          mosaic: Mosaic,
                          bbox: BBox,
                          minimal: bool,
                          summary: bool) -> Response:
        quads_template = mosaic["_links"]["quads"]
        # this is fully qualified URL, so don't use self._url
        url = quads_template.replace("{lx},{ly},{ux},{uy}",
                                     ",".join([str(f) for f in bbox]))
        # params will overwrite the templated query
        if minimal:
            url += "&minimal=true"
        if summary:
            url += "&summary=true"
        return await self._session.request(
            method="GET",
            url=url,
        )

    async def get_quad(self, mosaic: Union[Mosaic, str], quad_id: str) -> Quad:
        """
        Get a mosaic's quad information.

        Example:

        ```python
        quad = await client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        print(quad)
        ```
        """
        mosaic = await self._resolve_mosaic(mosaic)
        mosaic_id = mosaic["id"]
        resp = await self._session.request(
            method="GET",
            url=self._url(f"mosaics/{mosaic_id}/quads/{quad_id}"),
        )
        return Quad(resp.json())

    async def get_quad_contributions(self, quad: Quad) -> list[dict]:
        """
        Get a mosaic's quad information.

        Example:

        ```python
        quad = await client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        contributions = await client.get_quad_contributions(quad)
        print(contributions)
        ```
        """
        resp = await self._session.request(
            "GET",
            quad["_links"]["items"],
        )
        return resp.json()["items"]

    async def download_quad(self,
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
        quad = await client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        await client.download_quad(quad)
        ```
        """
        url = quad["_links"]["download"]
        Path(directory).mkdir(exist_ok=True, parents=True)
        dest = Path(directory, quad["id"] + ".tif")
        # this avoids a request to the download endpoint which would
        # get counted as a download even if only the headers were read
        # and the response content is ignored (like if when the file
        # exists and overwrite is False)
        if dest.exists() and not overwrite:
            return
        async with self._session.stream(method='GET', url=url) as resp:
            await StreamingBody(resp).write(
                dest,
                # pass along despite our manual handling
                overwrite=overwrite,
                progress_bar=progress_bar)

    async def download_quads(self,
                             /,
                             mosaic: Union[Mosaic, str],
                             *,
                             directory: Optional[str] = None,
                             overwrite: bool = False,
                             bbox: Optional[BBox] = None,
                             geometry: Optional[Union[dict,
                                                      GeoInterface]] = None,
                             progress_bar: bool = False,
                             concurrency: int = 4):
        """
        Download a mosaics' quads to a directory.

        Raises:
            ClientError: if `geometry` or `bbox` is not specified.

        Example:

        ```python
        mosaic = await cl.get_mosaic(name)
        client.download_quads(mosaic, bbox=(-100, 40, -100, 40))
        ```
        """
        if not any((bbox, geometry)):
            raise ClientError("bbox or geometry is required")
        jobs = []
        mosaic = await self._resolve_mosaic(mosaic)
        directory = directory or mosaic["name"]
        async for q in self.list_quads(mosaic,
                                       minimal=True,
                                       bbox=bbox,
                                       geometry=geometry):
            jobs.append(
                self.download_quad(q,
                                   directory=directory,
                                   overwrite=overwrite,
                                   progress_bar=progress_bar))
            if len(jobs) == concurrency:
                await asyncio.gather(*jobs)
                jobs = []
        await asyncio.gather(*jobs)
