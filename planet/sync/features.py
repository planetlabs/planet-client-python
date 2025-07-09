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

from typing import Iterator, Optional, Union
from planet.clients.features import FeaturesClient
from planet.http import Session
from planet.models import Feature, GeoInterface


class FeaturesAPI:

    _client: FeaturesClient

    def __init__(self, session: Session, base_url: Optional[str] = None):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production Features API
                base url.
        """
        self._client = FeaturesClient(session, base_url)

    def list_collections(self, limit: int = 0) -> Iterator[dict]:
        """
        List the feature collections you have access to.

        Example:

        ```
        pl = Planet()
        collections = pl.features.list_collections()
        for collection in collections:
            print(collection)
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_collections(limit=limit))

    def get_collection(self, collection_id: str) -> dict:
        """
        Get collection metadata.

        note: when looking up or adding features to a collection,
        you can pass the collection ID directly to the add_features
        or list_features methods. It is not necessary to look up
        the collection metadata first.
        """
        collection = self._client.get_collection(collection_id)
        return self._client._call_sync(collection)

    def create_collection(self,
                          title: str,
                          description: Optional[str] = None) -> str:
        """
        Create a new collection with the given title and description, returning the collection id.

        Example:

        ```
        pl = Planet()
        collection_id = pl.features.create_collection(
          title="My Collection",
          description="a test collection"
        )
        ```
        """
        collection = self._client.create_collection(title, description)
        return self._client._call_sync(collection)

    def delete_collection(self, collection_id: str) -> None:
        """
        Delete a collection.

        Parameters:
            collection_id: The ID of the collection to delete

        Example:

        ```
        pl = Planet()
        pl.features.delete_collection(collection_id="my-collection")
        ```
        """
        return self._client._call_sync(
            self._client.delete_collection(collection_id))

    def list_items(self,
                   collection_id: str,
                   limit: int = 0) -> Iterator[Feature]:
        """
        List features in `collection_id`.

        Returns an iterator of Features, which are `dict` instances with a
        convenience method/property for getting a feature reference (`.ref`).
        The reference can be used in the Data, Orders and Subscriptions
        APIs. Within the Python SDK, the entire Feature can generally be
        passed to functions that accept a geometry.

        example:

        ```
        pl = Planet()
        features = pl.features.list_items(collection_id)
        for feature in features:
            print(feature.ref)
            print(feature["id"])
            print(feature["geometry"])

            # use a feature directly in a search
            results = pl.data.search(["PSScene"], geometry=feature])
        ```
        """
        return self._client._aiter_to_iter(
            self._client.list_items(collection_id, limit=limit))

    def get_item(self, collection_id: str, feature_id: str) -> Feature:
        """
        Return metadata for a single feature in a collection
        """
        return self._client._call_sync(
            self._client.get_item(collection_id, feature_id))

    def delete_item(self, collection_id: str, feature_id: str) -> None:
        """
        Delete a feature from a collection.

        Parameters:
            collection_id: The ID of the collection containing the feature
            feature_id: The ID of the feature to delete

        Example:

        ```
        pl = Planet()
        pl.features.delete_item(collection_id="my-collection", feature_id="feature-123")
        ```
        """
        return self._client._call_sync(
            self._client.delete_item(collection_id, feature_id))

    def add_items(self,
                  collection_id: str,
                  feature: Union[dict, GeoInterface],
                  property_id: Optional[str] = None) -> list[str]:
        """
        Add a Feature or FeatureCollection to the collection given by `collection_id`.
        Returns a list of feature references.

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
        new_features = pl.features.add_items(
          collection_id="my-collection",
          feature=feature,
        )
        ```

        note: if a geojson Geometry is supplied, it will be converted
        to a Feature. However, we recommend doing this conversion yourself
        so that you can set a title and description property.

        The return value is always a list of references, even if you only upload one
        feature.
        """
        uploaded_features = self._client.add_items(collection_id,
                                                   feature,
                                                   property_id)

        return self._client._call_sync(uploaded_features)
