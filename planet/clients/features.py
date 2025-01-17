"""Planet Features API Python client."""

import logging
from typing import Any, AsyncIterator, Optional

from planet.exceptions import APIError, ClientError
from planet.http import Session
from planet.models import Paged
from planet.constants import PLANET_BASE_URL

BASE_URL = f'{PLANET_BASE_URL}/features/v1/ogc/my/'

LOGGER = logging.getLogger()


class FeaturesClient:
    """Asyncronous Features API client

    For more information about the Features API, see the documentation at
    https://developers.planet.com/docs/apis/features/

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
        self._session = session

        self._base_url = base_url or BASE_URL
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    async def list_collections(self) -> AsyncIterator[dict]:
        """
        list the feature collections you have access to.
        
        Example:

        ```
        results = await client.list_collections()
        async for collection in results:
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
                                            self._session.request):
            yield col

    async def list_features(
            self,
            collection_id,
            limit: int = 10,
        ) -> AsyncIterator[dict]:
        """
        list features in `collection_id`.

        example:

        ```
        results = await client.list_features(collection_id)
        async for feature in results:
            print(feature)
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

        params: dict[str, Any] = {}
        url = f'{self._base_url}/collections/{collection_id}/items'

        resp = await self._session.request(method='GET',
                                            url=url,
                                            params=params)
        async for feat in _FeaturesPager(resp,
                                            self._session.request,
                                            limit=limit):
            yield feat

    async def create_collection(self, title: str, description: Optional[str] = None) -> str:
        """
        create a new collection with the given title and description, returning the collection id.

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

        resp = await self._session.request(method='POST',
                                               url=url,
                                               json=body)

        return resp.json()["id"]

    async def add_features(
            self,
            collection_id,
            feature: dict,
            property_id: Optional[str] = None) -> AsyncIterator[str]:
        """
        add a Feature or FeatureCollection to the collection given by `collection_id`.

        collection_id: the collection to add the feature to
        feature: a dict containing a geojson Feature or FeatureCollection.
        property_id (optional): the name of a property in the `properties` block of 
          the supplied feature(s). The value will become the feature's id.

        When the feature is added to the collection, it will be given an ID.
        The ID can be overriden by providing an `id` in the feature's properties.
        Title and description can also be set this way using the `title` and 
        `description` properties.

        Example:

        ```
        feature = {
          "type": "Feature",
          "geometry": {
            "coordinates": [
              [
                [
                  7.05322265625,
                  46.81509864599243
                ],
                [
                  7.580566406250001,
                  46.81509864599243
                ],
                [
                  7.580566406250001,
                  47.17477833929903
                ],
                [
                  7.05322265625,
                  47.17477833929903
                ],
                [
                  7.05322265625,
                  46.81509864599243
                ]
              ]
            ],
            "type": "Polygon"
          },
          "properties": {
            "id": "feature-1",
            "title": "Feature 1",
            "description": "Test feature"
          }
        }
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

        url = f'{self._base_url}/collections/{collection_id}/items'
        params: dict[str, Any] = {}
        if property_id:
            params["property_id"] = property_id

        if feature.get("type") in ["point", "multipoint", "polygon", "multipolygon", "linestring", "multilinestring"]:
            feature = {"type": "Feature", "geometry": feature}

        resp = await self._session.request(method='POST',
                                            url=url,
                                            json=feature,
                                            params=params)
        for fid in resp.json():
            yield fid
