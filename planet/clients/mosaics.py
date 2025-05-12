import asyncio
from pathlib import Path
from typing import AsyncIterator, Awaitable, Optional, Tuple, Type, TypeVar, Union, cast
from planet.constants import PLANET_BASE_URL
from planet.http import Session
from planet.models import Paged, Response, StreamingBody
from uuid import UUID

BASE_URL = f'{PLANET_BASE_URL}/basemaps/v1'

T = TypeVar("T")

Number = Union[int, float]

BBox = Tuple[Number, Number, Number, Number]


class Series(Paged):
    ITEMS_KEY = 'series'
    NEXT_KEY = '_next'


class Mosaics(Paged):
    ITEMS_KEY = 'mosaics'
    NEXT_KEY = '_next'


class MosaicQuads(Paged):
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
            base_url: The base URL to use. Defaults to production orders API
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
                           name: str) -> Optional[dict]:
        response = await self._session.request(
            method='GET',
            url=self._url(path),
            params={
                "name__is": name,
            },
        )
        listing = response.json()[pager.ITEMS_KEY]
        return listing[0] if listing else None

    async def _get_by_id(self, path: str, id: str) -> dict:
        response = await self._session.request(method="GET",
                                               url=self._url(f"{path}/{id}"))
        return response.json()

    async def _get(self, name_or_id: str, path: str,
                   pager: Type[Paged]) -> Optional[dict]:
        if _is_uuid(name_or_id):
            return await self._get_by_id(path, name_or_id)
        return await self._get_by_name(path, pager, name_or_id)

    async def get_mosaic(self, name_or_id: str) -> Optional[dict]:
        """Get the API representation of a mosaic by name or id.

        :param name str: The name or id of the mosaic
        :returns: dict or None (if searching by name)
        :raises planet.api.exceptions.APIException: On API error.
        """
        return await self._get(name_or_id, "mosaics", Mosaics)

    async def get_series(self, name_or_id: str) -> Optional[dict]:
        """Get the API representation of a series by name or id.

        :param name str: The name or id of the series
        :returns: dict or None (if searching by name)
        :raises planet.api.exceptions.APIException: On API error.
        """
        return await self._get(name_or_id, "series", Series)

    async def list_series(
            self,
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
        async for item in Series(resp, self._session.request):
            yield item

    async def list_mosaics(
        self,
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
        mosaics = await client.list_mosacis()
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
        async for item in Mosaics(resp, self._session.request):
            yield item

    async def list_series_mosaics(
        self,
        name_or_id: str,
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
        if not _is_uuid(name_or_id):
            series = await self._get_by_name("series", Series, name_or_id)
            if series is None:
                return
            name_or_id = series["id"]
        params = {}
        if acquired_gt:
            params["acquired__gt"] = acquired_gt
        if acquired_lt:
            params["acquired__lt"] = acquired_lt
        if latest:
            params["latest"] = "yes"
        resp = await self._session.request(
            method="GET",
            url=self._url(f"series/{name_or_id}/mosaics"),
            params=params,
        )
        async for item in Mosaics(resp, self._session.request):
            yield item

    async def list_quads(self,
                         mosaic: dict,
                         minimal: bool = False,
                         bbox: Optional[BBox] = None,
                         geometry: Optional[dict] = None,
                         summary: bool = False) -> AsyncIterator[dict]:
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
        async for item in MosaicQuads(resp, self._session.request):
            yield item

    async def _quads_geometry(self,
                              mosaic: dict,
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
                          mosaic: dict,
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

    async def get_quad(self, name_or_id: str, quad_id: str) -> dict:
        """
        Get a mosaic's quad information.

        Example:

        ```
        quad = await client.get_quad("d5098531-aa4f-4ff9-a9d5-74ad4a6301e5", "1234-5678")
        print(quad)
        ```
        """
        if not _is_uuid(name_or_id):
            mosaic = await self.get_mosaic(name_or_id)
            if mosaic is None:
                return {}
            name_or_id = cast(str, mosaic["id"])
        resp = await self._session.request(
            method="GET",
            url=self._url(f"mosaics/{name_or_id}/quads/{quad_id}"),
        )
        return resp.json()

    async def get_quad_contributions(self, quad: dict) -> list[dict]:
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
                            quad: dict,
                            directory,
                            overwrite: bool = False,
                            progress_bar=False):
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
        await client.download_quad(quad, ".")
        ```
        """

    async def download_quads(self,
                             mosaic: dict,
                             directory: str,
                             bbox: Optional[BBox] = None,
                             geometry: Optional[dict] = None,
                             progress_bar: bool = False,
                             concurrency: int = 4):
        """
        Download a mosaics' quads to a directory.

        Example:

        ```
        mosaic = await cl.get_mosaic(name)
        client.download_quads(mosaic, '.', bbox=(-100, 40, -100, 41))
        ```
        """
        jobs = []
        async for q in self.list_quads(mosaic,
                                       minimal=True,
                                       bbox=bbox,
                                       geometry=geometry):
            jobs.append(
                self.download_quad(q, directory, progress_bar=progress_bar))
            if len(jobs) == concurrency:
                await asyncio.gather(*jobs)
                jobs = []
        await asyncio.gather(*jobs)
