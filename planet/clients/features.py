"""Planet Features API Python client."""

import logging
from typing import AsyncIterator, Optional, Iterator

from planet.exceptions import APIError, ClientError
from planet.http import Session
from planet.models import Paged
from planet.constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/features/v1/ogc/my/'

LOGGER = logging.getLogger()


class FeaturesClient:
    """A Planet Features Service API 1.0.0 client.

    The methods of this class forward request parameters to the
    operations described in the Planet Features Service API 0.0.0
    (https://api.planet.com/features/v0/ogc/my/api) using HTTP 1.1.

    The methods generally return or yield Python dicts with the same
    structure as the JSON messages used by the service API. Many of the
    exceptions raised by this class are categorized by HTTP client
    (4xx) or server (5xx) errors. This client's level of abstraction is
    low.

    High-level asynchronous access to Planet's features API:

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('features')
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
            base_url: The base URL to use. Defaults to production features
                API base url.
        """
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    async def list_collections(self) -> AsyncIterator[dict]:

        class _CollectionsPager(Paged):
            """Navigates pages of messages about collections."""
            ITEMS_KEY = 'collections'
            LINKS_KEY = 'links'

            def _next_link(self, page):
                next_link = False

                # TODO: Build this into Paged.__next_link directly, other (unimplemented) APIs have a similar page structure
                for link in page[self.LINKS_KEY]:
                    if "rel" in link and link["rel"] == self.NEXT_KEY:
                        next_link = link["href"]
                        LOGGER.debug(f'next: {next_link}')
                if not next_link:
                    LOGGER.debug('end of the pages')
                return next_link

        url = f'{self._base_url}/collections'

        try:
            response = await self._session.request(method='GET', url=url)
            async for col in _CollectionsPager(response,
                                               self._session.request):
                yield col
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def list_features(
            self,
            collection_id,
            limit: int = 10,
            bbox: Optional[list[float]] = None,
            datetime: Optional[str] = None) -> AsyncIterator[dict]:

        class _FeaturesPager(Paged):
            """Navigates pages of messages about features."""
            ITEMS_KEY = 'features'
            LINKS_KEY = 'links'

            def _next_link(self, page):
                next_link = False

                #TODO: Build this into Paged.__next_link directly, other (unimplemented) APIs have a similar page structure
                for link in page[self.LINKS_KEY]:
                    if "rel" in link and link["rel"] == self.NEXT_KEY:
                        next_link = link["href"]
                        LOGGER.debug(f'next: {next_link}')
                if not next_link:
                    LOGGER.debug('end of the pages')
                return next_link

        params = {}
        if bbox:
            params["bbox"] = bbox
        if datetime:
            params["datetime"] = datetime
        url = f'{self._base_url}/collections/{collection_id}/items'

        try:
            resp = await self._session.request(method='GET',
                                               url=url,
                                               params=params)
            async for feat in _FeaturesPager(resp,
                                             self._session.request,
                                             limit=limit):
                yield feat
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def create_collection(self, request: dict) -> dict:
        url = f'{self._base_url}/collections'
        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request)
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            col = resp.json()
            return col

    async def add_features(
            self,
            collection_id,
            request: dict,
            bbox: Optional[list[float]] = None,
            datetime: Optional[str] = None,
            property_id: Optional[str] = None) -> AsyncIterator[str]:

        url = f'{self._base_url}/collections/{collection_id}/items'
        params = {}
        if bbox:
            params["bbox"] = bbox
        if datetime:
            params["datetime"] = datetime
        if property_id:
            params["property_id"] = property_id
        try:
            resp = await self._session.request(method='POST',
                                               url=url,
                                               json=request,
                                               params=params)
            for fid in resp.json():
                yield fid
        # Forward APIError. We don't strictly need this clause, but it
        # makes our intent clear.
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
