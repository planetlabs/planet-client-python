import asyncio
from pathlib import Path
from typing import AsyncIterator, Awaitable, Optional, Tuple, Type, TypeVar, Union, cast
from planet.constants import PLANET_BASE_URL
from planet.exceptions import MissingResource
from planet.http import Session
from planet.models import Mosaic, Paged, Quad, Response, Series, StreamingBody
from uuid import UUID

BASE_URL = f'{PLANET_BASE_URL}/basemaps/v1'

T = TypeVar("T")

Number = Union[int, float]

BBox = Tuple[Number, Number, Number, Number]


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


class MosaicsClient:
    """High-level asynchronous access to Planet's Mosaics API.

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('data')
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
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def _call_sync(self, f: Awaitable[T]) -> T:
        """block on an async function call, using the call_sync method of the session"""
        return self._session._call_sync(f)

    def _url(self, path: str) -> str:
        return f"{BASE_URL}/{path}"

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
        raise MissingResource(f"{name} not found")

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

        :param name str: The name or id of the mosaic
        :returns: dict or None (if searching by name)
        :raises planet.api.exceptions.APIException: On API error.
        """
        return Mosaic(await self._get(name_or_id, "mosaics", _MosaicsPage))

    async def get_series(self, name_or_id: str) -> Series:
        """Get the API representation of a series by name or id.

        :param name str: The name or id of the series
        :returns: dict or None (if searching by name)
        :raises planet.api.exceptions.APIException: On API error.
        """
        return Series(await self._get(name_or_id, "series", _SeriesPage))

    async def list_series(
            self,
            *,
            name_contains: Optional[str] = None,
            interval: Optional[str] = None,
            acquired_gt: Optional[str] = None,
            acquired_lt: Optional[str] = None) -> AsyncIterator[dict]:
        """
        List the series you have access to.

        Example:

        ```
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
            yield item

    async def list_mosaics(
        self,
        *,
        name_contains: Optional[str] = None,
        interval: Optional[str] = None,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
        latest: bool = False,
    ) -> AsyncIterator[dict]:
        """
        List the mosaics you have access to.

        Example:

        ```
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
        if latest:
            params["latest"] = "yes"
        resp = await self._session.request(
            method='GET',
            url=self._url("mosaics"),
            params=params,
        )
        async for item in _MosaicsPage(resp, self._session.request):
            yield item

    async def list_series_mosaics(
        self,
        /,
        series: Union[Series, str],
        *,
        acquired_gt: Optional[str] = None,
        acquired_lt: Optional[str] = None,
        latest: bool = False,
    ) -> AsyncIterator[dict]:
        """
        List the mosaics in a series.

        Example:

        ```
        mosaics = await client.list_series_mosaics("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        async for m in mosaics:
            print(m)
        ```
        """
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
            yield item

    async def list_quads(self,
                         /,
                         mosaic: Union[Mosaic, str],
                         *,
                         minimal: bool = False,
                         bbox: Optional[BBox] = None,
                         geometry: Optional[dict] = None,
                         summary: bool = False) -> AsyncIterator[Quad]:
        """
        List the a mosaic's quads.

        Example:

        ```
        mosaic = await client.get_mosaic("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5")
        quads = await client.list_quads(mosaic)
        async for q in quads:
            print(q)
        ```
        """
        mosaic = await self._resolve_mosaic(mosaic)
        if geometry:
            resp = await self._quads_geometry(mosaic,
                                              geometry,
                                              minimal,
                                              summary)
        else:
            if bbox is None:
                xmin, ymin, xmax, ymax = cast(BBox, mosaic['bbox'])
                search = (max(-180, xmin),
                          max(-85, ymin),
                          min(180, xmax),
                          min(85, ymax))
            else:
                search = bbox
            resp = await self._quads_bbox(mosaic, search, minimal, summary)
        # kinda yucky - yields a different "shaped" dict
        if summary:
            yield resp.json()["summary"]
            return
        async for item in _QuadsPage(resp, self._session.request):
            yield Quad(item)

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

        ```
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

        ```
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
        url = quad["_links"]["download"]
        Path(directory).mkdir(exist_ok=True, parents=True)
        async with self._session.stream(method='GET', url=url) as resp:
            body = StreamingBody(resp)
            dest = Path(directory, body.name)
            await body.write(dest,
                             overwrite=overwrite,
                             progress_bar=progress_bar)
        """
        Download a quad to a directory.

        Example:

        ```
        quad = await client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        await client.download_quad(quad)
        ```
        """

    async def download_quads(self,
                             /,
                             mosaic: Union[Mosaic, str],
                             *,
                             directory: Optional[str] = None,
                             overwrite: bool = False,
                             bbox: Optional[BBox] = None,
                             geometry: Optional[dict] = None,
                             progress_bar: bool = False,
                             concurrency: int = 4):
        """
        Download a mosaics' quads to a directory.

        Example:

        ```
        mosaic = await cl.get_mosaic(name)
        client.download_quads(mosaic, bbox=(-100, 40, -100, 41))
        ```
        """
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
