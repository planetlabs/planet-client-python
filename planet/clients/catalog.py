"""Planet Catalog API client."""

import logging

from typing import Optional

from planet.clients.base import _BaseClient
from planet.exceptions import APIError, ClientError
from planet.http import Session
from ..constants import SENTINEL_HUB_BASE_URL

BASE_URL = f'{SENTINEL_HUB_BASE_URL}/api/v1/catalog/1.0.0'

LOGGER = logging.getLogger()

class CatalogClient(_BaseClient):
    """To do - add class docstring."""

    def __init__(self,
                 session: Session,
                 base_url: Optional[str] = None) -> None:
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production subscriptions
                API base url.
        """
        super().__init__(session, base_url or BASE_URL)

    async def get_info(self) -> dict:
        """Provides the main information that define Sentinel Hub Catalog API

        `Catalog API reference <https://docs.sentinel-hub.com/api/latest/reference/#operation/getLandingPage>`

        :return: A service payload with information
        """
        try:
            resp = await self._session.request(method='GET', url=self._base_url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            info = resp.json()
            return info

    async def get_conformance(self) -> dict:
        """Get information about specifications that this API conforms to

        `Catalog API reference
        <https://docs.sentinel-hub.com/api/latest/reference/#operation/getConformanceDeclaration>`

        :return: A service payload with conformance information
        """
        try:
            url = f'{self._base_url}/conformance'
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            conformance = resp.json()
            return conformance

    async def get_collections(self) -> dict:
        """Provides a list of collections that are available to a user

        `Catalog API reference <https://docs.sentinel-hub.com/api/latest/reference/#operation/getCollections>`__

        :return: A list of collections with information
        """
        try:
            url = f'{self._base_url}/collections'
            resp = await self._session.request(method='GET', url=url)
        except APIError:
            raise
        except ClientError:  # pragma: no cover
            raise
        else:
            collections = resp.json()
            return collections

"""
OpenAPI Specification
---------------------
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/conformance
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/collections
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/collections/{collectionId}
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/collections/{collectionId}/queryables
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/collections/{collectionId}/items
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/collections/{collectionId}/items/{featureId}
* GET  https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search
* POST https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search
"""