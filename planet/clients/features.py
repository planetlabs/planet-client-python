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
from typing import Any, AsyncIterator, Optional, Union, TypeVar

from planet.clients.base import _BaseClient
from planet.exceptions import ClientError
from planet.http import Session
from planet.models import Feature, GeoInterface, Paged
from planet.constants import PLANET_BASE_URL

T = TypeVar("T")

BASE_URL = f'{PLANET_BASE_URL}/features/v1/ogc/my/'

LOGGER = logging.getLogger()


class FeaturesClient(_BaseClient):
    """Asyncronous Features API client

    For more information about the Features API, see the documentation at
    https://docs.planet.com/develop/apis/features/

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
            base_url: The base URL to use. Defaults to the Features
                API base url at api.planet.com.
        """
        super().__init__(session, base_url or BASE_URL)

    async def list_collections(self, limit: int = 0) -> AsyncIterator[dict]:
        """
        List the feature collections you have access to.

        Example:

        ```
        collections = await client.list_collections()
        async for collection in collections:
            print(collection)
        ```
        """

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

        response = await self._session.request(method='GET', url=url)
        async for col in _CollectionsPager(response,
                                           self._session.request,
                                           limit=limit):
            yield col

    async def get_collection(self, collection_id: str) -> dict:
        """
        Get collection metadata.

        note: when looking up or adding features to a collection,
        you can pass the collection ID directly to the add_features
        or list_features methods. It is not necessary to look up
        the collection metadata first.
        """
        url = f'{self._base_url}/collections/{collection_id}'
        response = await self._session.request(method='GET', url=url)
        return response.json()

    async def list_items(
        self,
        collection_id: str,
        limit: int = 10,
    ) -> AsyncIterator[Feature]:
        """
        List features in `collection_id`.

        Returns an iterator of Features, which are `dict` instances with a
        convenience method/property for getting a feature reference (`.ref`).
        The reference can be used in the Data, Orders and Subscriptions
        APIs. Within the Python SDK, the entire Feature can generally be
        passed to functions that accept a geometry.

        example:

        ```
        results = await client.list_items(collection_id)
        async for feature in results:
            print(feature.ref)
            print(feature["id"])
            print(feature["geometry"])
        ```
        """

        class _FeaturesPager(Paged):
            """Navigates pages of messages about features."""
            ITEMS_KEY = 'features'
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

        url = f'{self._base_url}/collections/{collection_id}/items'

        resp = await self._session.request(method='GET', url=url)
        async for feat in _FeaturesPager(resp,
                                         self._session.request,
                                         limit=limit):
            yield Feature(**feat)

    async def get_item(self, collection_id: str, feature_id: str) -> Feature:
        """
        Return metadata for a single feature in a collection
        """
        url = f'{self._base_url}/collections/{collection_id}/items/{feature_id}'
        response = await self._session.request(method='GET', url=url)
        return Feature(**response.json())

    async def delete_item(self, collection_id: str, feature_id: str) -> None:
        """
            Delete a feature from a collection.

            Parameters:
                collection_id: The ID of the collection containing the feature
                feature_id: The ID of the feature to delete

            Example:

            ```
            await features_client.delete_item(
                collection_id="my-collection",
                feature_id="feature-123"
            )
            ```
            """

        # fail early instead of sending a delete request without a feature id.
        if len(feature_id) < 1:
            raise ClientError("Must provide a feature id")

        url = f'{self._base_url}/collections/{collection_id}/items/{feature_id}'
        await self._session.request(method='DELETE', url=url)

    async def create_collection(self,
                                title: str,
                                description: Optional[str] = None) -> str:
        """
        Create a new collection with the given title and description, returning the collection id.

        Example:

        ```
        collection_id = await features_client.create_collection(
          title="My Collection",
          description="a test collection"
        )
        ```
        """
        url = f'{self._base_url}/collections'
        body = {"title": title}

        if description:
            body["description"] = description

        resp = await self._session.request(method='POST', url=url, json=body)

        return resp.json()["id"]

    async def delete_collection(self, collection_id: str) -> None:
        """
        Delete a collection.

        Parameters:
            collection_id: The ID of the collection to delete

        Example:

        ```
        await features_client.delete_collection(
            collection_id="my-collection"
        )
        ```
        """

        # fail early instead of sending a delete request without a collection id.
        if len(collection_id) < 1:
            raise ClientError("Must provide a collection id")

        url = f'{self._base_url}/collections/{collection_id}'
        await self._session.request(method='DELETE', url=url)

    async def add_items(self,
                        collection_id: str,
                        feature: Union[dict, GeoInterface],
                        property_id: Optional[str] = None) -> list[str]:
        """
        Add a Feature or FeatureCollection to the collection given by `collection_id`.
        Returns a list of feature references.

        Features API only accepts Polygon and MultiPolygon.

        collection_id: the collection to add the feature to
        feature: a dict containing a geojson Feature or FeatureCollection, or an
          instance of a class that implements __geo_interface__ (e.g. a Shapely or
          GeoPandas geometry object)
        property_id (optional): the name of a property in the `properties` block of
          the supplied feature(s). The value will become the feature's id.

        When the feature is added to the collection, it will be given an ID.
        The ID can be overriden by providing an `id` in the feature's properties.
        Title and description can also be set this way using the `title` and
        `description` properties.

        Example:

        ```
        new_features = await features_client.add_features(
          collection_id="my-collection",
          feature=feature,
        )
        ```

        note: if a geojson Geometry is supplied, it will be converted
        to a Feature. However, we recommend doing this conversion yourself
        so that you can set a title and description property.

        The return value is always an iterator, even if you only upload one
        feature.
        """
        if isinstance(feature, GeoInterface):
            # we expect __geo_interface__ to return a Geometry (not a Feature), so
            # we're using the name `feature` liberally. We'll convert to a feature
            # at the next step.
            feature = feature.__geo_interface__

        # convert a geojson geometry into geojson feature
        if feature.get("type",
                       "").lower() not in ["feature", "featurecollection"]:
            feature = {"type": "Feature", "geometry": feature}

        url = f'{self._base_url}/collections/{collection_id}/items'
        params: dict[str, Any] = {}
        if property_id:
            params["property_id"] = property_id

        resp = await self._session.request(method='POST',
                                           url=url,
                                           json=feature,
                                           params=params)
        return list(resp.json())
