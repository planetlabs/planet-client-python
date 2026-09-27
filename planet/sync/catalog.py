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
"""Synchronous Planet Catalog API client."""

from typing import Any, Dict, Iterator, List, Optional, Union

from planet.clients.catalog import CatalogClient
from planet.http import Session


class CatalogAPI:
    """Catalog API client.

    Note:
        Unlike the other Planet APIs, the Catalog API is not served from
        `api.planet.com`. It is hosted by Sentinel Hub and authenticates with
        an OAuth bearer token, so a plain Planet API key will not work.

    Example:
        ```python
        >>> from planet import Planet
        >>>
        >>> pl = Planet()
        >>> for item in pl.catalog.search(
        ...         collections=['sentinel-2-l2a'],
        ...         datetime='2020-12-10T00:00:00Z/2020-12-30T00:00:00Z',
        ...         bbox=[13, 45, 14, 46]):
        ...     print(item['id'])
        ```
    """

    _client: CatalogClient

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to the production Catalog
                API base URL for the `eu-central-1` deployment.
        """
        self._client = CatalogClient(session, base_url)

    def get_landing_page(self) -> Dict[str, Any]:
        """Get the Catalog API landing page - the root STAC Catalog.

        See [planet.clients.catalog.CatalogClient.get_landing_page][] for
        details.
        """
        return self._client._call_sync(self._client.get_landing_page())

    def get_conformance(self) -> Dict[str, Any]:
        """Get the specifications this API conforms to.

        See [planet.clients.catalog.CatalogClient.get_conformance][] for
        details.
        """
        return self._client._call_sync(self._client.get_conformance())

    def list_collections(self) -> List[Dict[str, Any]]:
        """List the collections available to your account.

        See [planet.clients.catalog.CatalogClient.list_collections][] for
        details.
        """
        return self._client._call_sync(self._client.list_collections())

    def get_collection(self, collection_id: str) -> Dict[str, Any]:
        """Describe a single collection.

        See [planet.clients.catalog.CatalogClient.get_collection][] for
        details.
        """
        return self._client._call_sync(
            self._client.get_collection(collection_id))

    def get_collection_queryables(self, collection_id: str) -> Dict[str, Any]:
        """Get the properties a collection can be filtered on.

        See [planet.clients.catalog.CatalogClient.get_collection_queryables][]
        for details.
        """
        return self._client._call_sync(
            self._client.get_collection_queryables(collection_id))

    def list_items(
        self,
        collection_id: str,
        bbox: Optional[List[float]] = None,
        datetime: Optional[str] = None,
        limit: int = 100,
        page_size: int = 100,
    ) -> Iterator[dict]:
        """Iterate over the items in a collection.

        See [planet.clients.catalog.CatalogClient.list_items][] for parameter
        details.
        """
        return self._client._aiter_to_iter(
            self._client.list_items(collection_id,
                                    bbox=bbox,
                                    datetime=datetime,
                                    limit=limit,
                                    page_size=page_size))

    def get_item(self, collection_id: str, item_id: str) -> Dict[str, Any]:
        """Get a single item from a collection.

        See [planet.clients.catalog.CatalogClient.get_item][] for details.
        """
        return self._client._call_sync(
            self._client.get_item(collection_id, item_id))

    def simple_search(
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
    ) -> Iterator[dict]:
        """Search items with simple filtering (`GET /search`).

        See [planet.clients.catalog.CatalogClient.simple_search][] for
        parameter details.
        """
        return self._client._aiter_to_iter(
            self._client.simple_search(collections,
                                       datetime,
                                       bbox=bbox,
                                       intersects=intersects,
                                       ids=ids,
                                       fields=fields,
                                       filter=filter,
                                       distinct=distinct,
                                       limit=limit,
                                       page_size=page_size))

    def search(
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
    ) -> Iterator[dict]:
        """Search items with full-featured filtering (`POST /search`).

        See [planet.clients.catalog.CatalogClient.search][] for parameter
        details.
        """
        return self._client._aiter_to_iter(
            self._client.search(collections,
                                datetime,
                                bbox=bbox,
                                intersects=intersects,
                                ids=ids,
                                fields=fields,
                                filter=filter,
                                filter_lang=filter_lang,
                                filter_crs=filter_crs,
                                distinct=distinct,
                                limit=limit,
                                page_size=page_size))
