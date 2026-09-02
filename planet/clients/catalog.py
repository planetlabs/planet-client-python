# Copyright 2026 Planet Labs PBC.
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
"""Planet Catalog API Python client."""

import json
import logging
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional, Union

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError, PagingError
from planet.http import Session
from planet.models import Paged
from ..constants import SENTINEL_HUB_BASE_URL, SENTINEL_HUB_US_WEST_2_BASE_URL

BASE_URL = f'{SENTINEL_HUB_BASE_URL}/catalog/v1'
US_WEST_2_BASE_URL = f'{SENTINEL_HUB_US_WEST_2_BASE_URL}/catalog/v1'

LOGGER = logging.getLogger()


class _CatalogPaged(Paged):
    """Pager for Catalog API GET responses.

    Catalog API item responses are STAC ItemCollections: the items are under
    `features` and the paging link is the entry with `"rel": "next"` in the
    top-level `links` list.
    """
    LINKS_KEY = 'links'
    ITEMS_KEY = 'features'

    def _next_link(self, page):
        for link in page.get(self.LINKS_KEY) or []:
            if link.get('rel') == self.NEXT_KEY and link.get('href'):
                LOGGER.debug(f'next: {link["href"]}')
                return link['href']
        LOGGER.debug('end of the pages')
        return False


class _CatalogSearchPaged(_CatalogPaged):
    """Pager for `POST /search`, which cannot be paged by following a link.

    The Catalog API pages item search by returning a `context.next` token; the
    next page is retrieved by re-sending the original query with `next` added.
    """

    def __init__(self,
                 response,
                 request_fcn,
                 url: str,
                 body: Dict[str, Any],
                 limit: int = 0):
        self._url = url
        self._body = body
        super().__init__(response, request_fcn, limit=limit)

    @staticmethod
    def _next_token(page) -> Union[str, bool]:
        next_token = (page.get('context') or {}).get('next')
        if not next_token:
            LOGGER.debug('end of the pages')
            return False
        LOGGER.debug(f'next: {next_token}')
        return next_token

    async def _get_pages(self, response) -> AsyncGenerator:
        page = response.json()
        yield page

        next_token = self._next_token(page)
        while next_token:
            LOGGER.debug('getting next page')
            response = await self._request_fcn(method='POST',
                                               url=self._url,
                                               json={
                                                   **self._body,
                                                   'next': next_token
                                               })
            page = response.json()

            # If the server echoes back the same token we would re-request the
            # same page forever. Mirrors the guard in planet.models.Paged.
            prev_token = next_token
            next_token = self._next_token(page)

            if next_token == prev_token:
                raise PagingError(
                    "Page cycle detected at {!r}".format(next_token))

            yield page


class CatalogClient(_BaseClient):
    """Asynchronous Catalog API client.

    The methods of this class forward request parameters to the operations
    described in the Planet Catalog API specification
    (https://docs.planet.com/develop/apis/catalog/reference/). The Catalog API
    is an implementation of the STAC (SpatioTemporal Asset Catalog)
    specification.

    Note:
        Unlike the other Planet APIs, the Catalog API is not served from
        `api.planet.com`. It is hosted by Sentinel Hub and authenticates with
        an OAuth bearer token, so a plain Planet API key will not work. Use an
        OAuth profile - see the client authentication documentation at
        https://docs.planet.com/develop/authentication/

    For more information, see the documentation at
    https://docs.planet.com/develop/apis/catalog/

    Example:
        ```python
        >>> import asyncio
        >>> from planet import Session
        >>>
        >>> async def main():
        ...     async with Session() as sess:
        ...         cl = sess.client('catalog')
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
            base_url: The base URL to use. Defaults to the production Catalog
                API base URL for the `eu-central-1` deployment
                (`https://services.sentinel-hub.com/catalog/v1`). Pass
                `planet.clients.catalog.US_WEST_2_BASE_URL` for the
                `us-west-2` deployment.
        """
        super().__init__(session, base_url or BASE_URL)
        self._collections_url = f'{self._base_url}/collections'
        self._search_url = f'{self._base_url}/search'

    @staticmethod
    def _query_params(**kwargs) -> Dict[str, Any]:
        """Build a query-string params dict, dropping unset values.

        The Catalog API declares its array and object query parameters with
        `explode: false`, so lists are comma-joined and geometries are sent as
        encoded JSON rather than as repeated parameters.
        """
        params: Dict[str, Any] = {}
        for key, value in kwargs.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                params[key] = ','.join(str(entry) for entry in value)
            elif isinstance(value, dict):
                params[key] = json.dumps(value)
            else:
                params[key] = value
        return params

    async def get_landing_page(self) -> dict:
        """Get the Catalog API landing page.

        The landing page is the root STAC Catalog. It is the entry point for
        browsing or crawling the catalog and describes the conformance classes
        the server implements.

        Returns:
            dict: the root STAC Catalog, including `conformsTo` and `links`.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        try:
            resp = await self._session.request(method='GET',
                                               url=self._base_url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def get_conformance(self) -> dict:
        """Get the specifications this API conforms to.

        Returns:
            dict: payload with a `conformsTo` list of conformance class URIs.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._base_url}/conformance'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def list_collections(self) -> List[dict]:
        """List the collections available to your account.

        Note:
            This endpoint is not paged - the API returns every accessible
            collection in a single response.

        Returns:
            list[dict]: the STAC Collections available to the requesting user.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        try:
            resp = await self._session.request(method='GET',
                                               url=self._collections_url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json().get('collections', [])

    async def get_collection(self, collection_id: str) -> dict:
        """Describe a single collection.

        Parameters:
            collection_id: Local identifier of the collection, e.g.
                `sentinel-2-l2a`.

        Returns:
            dict: the STAC Collection description, including its spatial and
                temporal extents and its `summaries`.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._collections_url}/{collection_id}'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def get_collection_queryables(self, collection_id: str) -> dict:
        """Get the properties a collection can be filtered on.

        The returned JSON Schema describes the variable terms that are valid
        in the CQL2 expressions accepted by the `filter` parameter of
        [planet.clients.catalog.CatalogClient.search][] and
        [planet.clients.catalog.CatalogClient.simple_search][].

        Parameters:
            collection_id: Local identifier of the collection.

        Returns:
            dict: a JSON Schema of the collection's queryable properties.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._collections_url}/{collection_id}/queryables'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def list_items(
        self,
        collection_id: str,
        bbox: Optional[List[float]] = None,
        datetime: Optional[str] = None,
        limit: int = 100,
        page_size: int = 100,
    ) -> AsyncIterator[dict]:
        """Iterate over the items in a collection.

        Parameters:
            collection_id: Local identifier of the collection.
            bbox: Only return items intersecting this bounding box, given in
                CRS84 as `[west, south, east, north]`, or as six values when
                the vertical bounds are included.
            datetime: An RFC 3339 date-time or interval. Open intervals use
                double-dots, e.g. `2018-02-12T00:00:00Z/..`.
            limit: Maximum number of items to return. When set to 0, no
                maximum is applied.
            page_size: Number of items to fetch per request. The API accepts
                1-100 and defaults to 10.

        Yields:
            dict: A STAC Item.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = self._query_params(bbox=bbox,
                                    datetime=datetime,
                                    limit=page_size)

        url = f'{self._collections_url}/{collection_id}/items'
        try:
            response = await self._session.request(method='GET',
                                                   url=url,
                                                   params=params)
            async for item in _CatalogPaged(response,
                                            self._session.request,
                                            limit=limit):
                yield item
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def get_item(self, collection_id: str, item_id: str) -> dict:
        """Get a single item from a collection.

        Parameters:
            collection_id: Local identifier of the collection.
            item_id: Local identifier of the item.

        Returns:
            dict: the STAC Item.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        url = f'{self._collections_url}/{collection_id}/items/{item_id}'
        try:
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        return resp.json()

    async def simple_search(
        self,
        collections: List[str],
        datetime: str,
        bbox: Optional[List[float]] = None,
        intersects: Optional[dict] = None,
        ids: Optional[List[str]] = None,
        fields: Optional[str] = None,
        filter: Optional[str] = None,
        distinct: Optional[str] = None,
        limit: int = 100,
        page_size: int = 100,
    ) -> AsyncIterator[dict]:
        """Search items with simple filtering (`GET /search`).

        This is the shorthand search operation. Its `filter` is CQL2 text and
        its `fields` is a comma-separated string. For CQL2 JSON filters,
        include/exclude field objects, or searching more than one collection,
        use [planet.clients.catalog.CatalogClient.search][] instead.

        Parameters:
            collections: Collection IDs to search. This operation accepts
                exactly one collection.
            datetime: An RFC 3339 date-time or interval. Required.
            bbox: Only return items intersecting this bounding box, in CRS84.
            intersects: Only return items intersecting this GeoJSON geometry.
            ids: Only return items with these IDs.
            fields: Comma-separated attributes to include or exclude, e.g.
                `id,type,-geometry,bbox,properties,-links,-assets`.
            filter: A CQL2 text filter, e.g. `eo:cloud_cover>90`. The
                filterable properties of a collection are given by
                [planet.clients.catalog.CatalogClient.get_collection_queryables][].
            distinct: Return the unique values of this property instead of
                full item metadata. The yielded values are the property values
                themselves rather than STAC Items.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.
            page_size: Number of results to fetch per request. The API accepts
                1-100 and defaults to 10.

        Yields:
            dict: A STAC Item, or a distinct property value when `distinct` is
                given.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        params = self._query_params(collections=collections,
                                    datetime=datetime,
                                    bbox=bbox,
                                    intersects=intersects,
                                    ids=ids,
                                    fields=fields,
                                    filter=filter,
                                    distinct=distinct,
                                    limit=page_size)

        try:
            response = await self._session.request(method='GET',
                                                   url=self._search_url,
                                                   params=params)
            async for item in _CatalogPaged(response,
                                            self._session.request,
                                            limit=limit):
                yield item
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise

    async def search(
        self,
        collections: List[str],
        datetime: str,
        bbox: Optional[List[float]] = None,
        intersects: Optional[dict] = None,
        ids: Optional[List[str]] = None,
        fields: Optional[Union[str, dict]] = None,
        filter: Optional[Union[str, dict]] = None,
        filter_lang: Optional[str] = None,
        filter_crs: Optional[str] = None,
        distinct: Optional[str] = None,
        limit: int = 100,
        page_size: int = 100,
    ) -> AsyncIterator[dict]:
        """Search items with full-featured filtering (`POST /search`).

        Parameters:
            collections: Collection IDs to search.
            datetime: An RFC 3339 date-time or interval. Required.
            bbox: Only return items intersecting this bounding box, in CRS84.
            intersects: Only return items intersecting this GeoJSON geometry.
            ids: Only return items with these IDs.
            fields: Attributes to include in the response, either as a
                comma-separated string or as a mapping with `include` and
                `exclude` lists, e.g.
                `{'include': ['id', 'bbox'], 'exclude': ['geometry']}`.
            filter: A CQL2 filter, given as text (e.g. `eo:cloud_cover>90`) or
                as a CQL2 JSON mapping. The filterable properties of a
                collection are given by
                [planet.clients.catalog.CatalogClient.get_collection_queryables][].
            filter_lang: The CQL2 encoding `filter` uses - `cql2-text` or
                `cql2-json`. Sent as `filter-lang`.
            filter_crs: The CRS used by spatial literals in `filter`. Sent as
                `filter-crs`.
            distinct: Return the unique values of this property instead of
                full item metadata. The yielded values are the property values
                themselves rather than STAC Items.
            limit: Maximum number of results to return. When set to 0, no
                maximum is applied.
            page_size: Number of results to fetch per request. The API accepts
                1-100 and defaults to 10.

        Yields:
            dict: A STAC Item, or a distinct property value when `distinct` is
                given.

        Raises:
            APIError: on an API server error.
            ClientError: on a client error.
        """
        body: Dict[str, Any] = {
            'collections': list(collections),
            'datetime': datetime,
            'limit': page_size,
        }
        optional: Dict[str, Any] = {
            'bbox': bbox,
            'intersects': intersects,
            'ids': ids,
            'fields': fields,
            'filter': filter,
            'filter-lang': filter_lang,
            'filter-crs': filter_crs,
            'distinct': distinct,
        }
        body.update({k: v for k, v in optional.items() if v is not None})

        try:
            response = await self._session.request(method='POST',
                                                   url=self._search_url,
                                                   json=body)
            async for item in _CatalogSearchPaged(response,
                                                  self._session.request,
                                                  url=self._search_url,
                                                  body=body,
                                                  limit=limit):
                yield item
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise


__all__ = ['CatalogClient']
