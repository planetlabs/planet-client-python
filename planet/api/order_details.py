# Copyright 2020 Planet Labs, Inc.
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
"""Functionality for preparing order details for use in creating an order"""
from __future__ import annotations  # https://stackoverflow.com/a/33533514
import copy
import json
import logging
from typing import List, Union

from .. import geojson, specs

LOGGER = logging.getLogger(__name__)


class OrderDetailsException(Exception):
    """Exceptions thrown by OrderDetails"""
    pass


class OrderDetails():
    '''Validating and preparing order details for submission.

    Can be built up from order detail parts:

    ```python
    >>> from planet.api.order_details import OrderDetails, Product
    >>>
    >>> image_ids = ['3949357_1454705_2020-12-01_241c']
    >>> order_detail = OrderDetails(
    ...     'test_order',
    ...     [Product(image_ids, 'analytic', 'psorthotile')]
    ... )
    ...

    ```

    or from a dict describing the order detail:

    ```python
    >>> order_detail_json = {
    ...     'name': 'test_order',
    ...     'products': [{'item_ids': ['3949357_1454705_2020-12-01_241c'],
    ...                   'item_type': 'PSOrthoTile',
    ...                   'product_bundle': 'analytic'}],
    ... }
    ...
    >>> order_detail = OrderDetails.from_dict(order_detail_json)

    ```
    '''
    def __init__(
        self,
        name: str,
        products: List[Product],
        subscription_id: int = 0,
        delivery: Delivery = None,
        notifications: Notifications = None,
        order_type: str = None,
        tools: List[Tool] = None
    ):
        """
        Parameters:
            name: Name of the order.
            products: Product(s) from the Data API to order.
            subscription_id: Apply this orders against this quota subscription.
            delivery: Specify custom delivery handling.
            notifications: Specify custom notifications handling.
            order_type: Accept a partial order, indicated by 'partial'.
            tools: Tools to apply to the products. Order defines
                the toolchain order of operatations.
        """
        self.name = name
        self.products = products
        self.subscription_id = subscription_id
        self.delivery = delivery
        self.notifications = notifications
        self.order_type = order_type
        self.tools = tools

        if self.order_type is not None:
            self.order_type = specs.validate_order_type(order_type)

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)

    @classmethod
    def from_dict(cls, details: dict) -> OrderDetails:
        """Create OrderDetails instance from Orders API spec representation.

        Parameters:
            details: API spec representation of OrderDetails.

        Returns:
            OrderDetails instance
        """
        name = details['name']
        products = [Product.from_dict(p) for p in details['products']]

        subscription_id = details.get('subscription_id', None)

        delivery = details.get('delivery', None)
        if delivery:
            delivery = Delivery.from_dict(delivery)

        notifications = details.get('notifications', None)
        if notifications:
            notifications = Notifications.from_dict(notifications)

        order_type = details.get('order_type', None)
        tools = [Tool.from_dict(t) for t in details.get('tools', [])]

        return cls(name,
                   products,
                   subscription_id,
                   delivery,
                   notifications,
                   order_type,
                   tools)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of OrderDetails.
        """
        details = {
            'name': self.name,
            'products': [p.to_dict() for p in self.products]
        }

        if self.subscription_id is not None:
            details['subscription_id'] = self.subscription_id

        if self.delivery is not None:
            details['delivery'] = self.delivery.to_dict()

        if self.notifications is not None:
            details['notifications'] = self.notifications.to_dict()

        if self.order_type is not None:
            details['order_type'] = self.order_type

        if self.tools is not None:
            details['tools'] = [t.to_dict() for t in self.tools]

        return details

    @property
    def json(self) -> str:
        '''Order details as a string representing json.'''
        return json.dumps(self.to_dict())


class Product():
    '''Product description for an order detail.'''

    def __init__(
        self,
        item_ids: List[str],
        product_bundle: str,
        item_type: str,
        fallback_bundle: str = None
    ):
        """
        Parameters:
            item_ids: IDs of the catalog items to include in the order.
            product_bundle: Set of asset types for the catalog items.
            item_type: The class of spacecraft and processing characteristics
                for the catalog items.
            fallback_bundle: In case product_bundle not having
                all asset types available, which would result in failed
                delivery, try a fallback bundle
        """
        self.item_ids = item_ids
        self.product_bundle = specs.validate_bundle(product_bundle)

        if fallback_bundle is not None:
            self.fallback_bundle = specs.validate_bundle(fallback_bundle)
        else:
            self.fallback_bundle = None

        self.item_type = specs.validate_item_type(item_type, product_bundle)
        if fallback_bundle is not None:
            specs.validate_item_type(item_type, fallback_bundle)

    @classmethod
    def from_dict(cls, details: dict) -> Product:
        """Create Product instance from Orders API spec representation.

        Parameters:
            details: API spec representation of product.

        Returns:
            Product instance
        """
        bundles = details['product_bundle'].split(',')
        product_bundle = bundles[0]
        try:
            fallback_bundle = bundles[1]
        except IndexError:
            fallback_bundle = None

        return cls(details['item_ids'],
                   product_bundle,
                   details['item_type'],
                   fallback_bundle)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of product.
        """
        product_bundle = self.product_bundle
        if self.fallback_bundle is not None:
            product_bundle = ','.join([product_bundle, self.fallback_bundle])
        product_dict = {
            'item_ids': self.item_ids,
            'item_type': self.item_type,
            'product_bundle': product_bundle
        }
        return product_dict


class Notifications():
    '''Notifications description for an order detail.'''
    def __init__(
        self,
        email: bool = False,
        webhook_url: str = None,
        webhook_per_order: bool = False
    ):
        """
        Parameters:
            email: Enable email notifications for an order.
            webhook_url: URL for notification when the order is ready.
            webhook_per_order: Request a single webhook call per order instead
                of one call per each delivered item.
        """
        self.email = email
        self.webhook_url = webhook_url
        self.webhook_per_order = webhook_per_order

    @classmethod
    def from_dict(cls, details: dict) -> Notifications:
        """Create Notifications instance from Orders API spec representation.

        Parameters:
            details: API spec representation of notifications.

        Returns:
            Notifications instance
        """
        return cls(**details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of notifications.
        """
        details = {}

        if self.email:
            details['email'] = self.email

        if self.webhook_url is not None:
            details['webhook_url'] = self.webhook_url

        if self.webhook_per_order:
            details['webhook_per_order'] = True

        return details


class Delivery():
    '''Manages order detail delivery description.'''
    def __init__(
        self,
        archive_type: str = None,
        single_archive: bool = False,
        archive_filename: str = None
    ):
        """
        Parameters:
            archive_type: Archive order files. Only supports 'zip'.
            single_archive: Archive all bundles together in a single file.
            archive_filename: Custom naming convention to use to name the
                archive file that is received. Uses the template variables
                {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        """
        if archive_type:
            self.archive_type = specs.validate_archive_type(archive_type)
        else:
            self.archive_type = archive_type

        self.single_archive = single_archive
        self.archive_filename = archive_filename

    @classmethod
    def from_file(
        cls,
        filename: str,
        subclass: bool = True
        ) -> Union[
                Delivery,
                AmazonS3Delivery,
                AzureBlobStorageDelivery,
                GoogleCloudStorageDelivery,
                GoogleEarthEngineDelivery]:
        """Create Delivery instance from file containing Orders API spec
        representation.

        Parameters:
            filename: Path to file.
            subclass: Create a subclass of Delivery if the necessary
                information is provided.

        Raises:
            FileNotFoundError: If filename does not exist.
            json.decoder.JSONDecodeError: If filename contents is not valid
                json.

        Returns:
            Delivery or Delivery subclass instance
        """
        with open(filename) as f:
            details = json.load(f)
        return cls.from_dict(details, subclass=subclass)

    @classmethod
    def from_dict(
        cls,
        details: dict,
        subclass: bool = True
        ) -> Union[
                Delivery,
                AmazonS3Delivery,
                AzureBlobStorageDelivery,
                GoogleCloudStorageDelivery,
                GoogleEarthEngineDelivery]:
        """Create Delivery instance from Orders API spec representation.

        Parameters:
            details: API spec representation of delivery.
            subclass: Create a subclass of Delivery if the necessary
                information is provided.

        Returns:
            Delivery or Delivery subclass instance
        """
        def _create_subclass(details):
            subclasses = [
                AmazonS3Delivery,
                AzureBlobStorageDelivery,
                GoogleCloudStorageDelivery,
                GoogleEarthEngineDelivery
                ]
            created = False
            for cls in subclasses:
                try:
                    created = cls.from_dict(details)
                except KeyError:
                    pass
                else:
                    break
            return created

        created = _create_subclass(details) or cls._from_dict(details)
        return created

    @classmethod
    def _from_dict(cls, details: dict) -> Delivery:
        """Create Delivery instance from Orders API spec representation.

        Parameters:
            details: API spec representation of delivery.

        Returns:
            Delivery instance
        """
        return cls(**details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of delivery.
        """
        details = {}

        if self.archive_type:
            details['archive_type'] = self.archive_type

        if self.single_archive:
            details['single_archive'] = self.single_archive

        if self.archive_filename:
            details['archive_filename'] = self.archive_filename

        return details


def _get_cloud_details(details, cloud_key):
    details = copy.deepcopy(details)
    cloud_details = details.pop(cloud_key)
    cloud_details.update(details)
    LOGGER.debug(f'cloud section of details: {cloud_details}')
    return cloud_details


class AmazonS3Delivery(Delivery):
    '''Amazon S3 delivery description for an order detail.'''

    cloud_key = 'amazon_s3'

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        bucket: str,
        aws_region: str,
        path_prefix: str = None,
        archive_type: str = False,
        single_archive: bool = False,
        archive_filename: str = None
    ):
        """
        Parameters:
            aws_access_key_id: S3 account access key.
            aws_secret_access_key: S3 account secret key.
            bucket: The name of the bucket that will receive the order output.
            aws_region: The region where the bucket lives in AWS.
            path_prefix: Custom string to prepend to the files delivered to the
                bucket. A slash (/) character will be treated as a "folder".
                Any other characters will be added as a prefix to the files.
            archive_type: Archive order files. Only supports 'zip'.
            single_archive: Archive all bundles together in a single file.
            archive_filename: Custom naming convention to use to name the
                archive file that is received. Uses the template variables
                {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.bucket = bucket
        self.path_prefix = path_prefix

        super().__init__(archive_type, single_archive, archive_filename)

    @classmethod
    def from_dict(cls, details: dict) -> AmazonS3Delivery:
        """Create AmazonS3Delivery instance from Orders API spec representation.

        Parameters:
            details: API spec representation of delivery.

        Returns:
            AmazonS3Delivery instance
        """
        cloud_details = _get_cloud_details(details, cls.cloud_key)
        return cls(**cloud_details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of AmazonS3Delivery.
        """
        cloud_details = {
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'bucket': self.bucket,
            'aws_region': self.aws_region,
        }

        if self.path_prefix:
            cloud_details['path_prefix'] = self.path_prefix

        details = super().to_dict()
        details[self.cloud_key] = cloud_details
        return details


class AzureBlobStorageDelivery(Delivery):
    '''Azure Blob Storage delivery description for an order detail.'''

    cloud_key = 'azure_blob_storage'

    def __init__(
        self,
        account: str,
        container: str,
        sas_token: str,
        storage_endpoint_suffix: str = None,
        path_prefix: str = None,
        archive_type: str = False,
        single_archive: bool = False,
        archive_filename: str = None
    ):
        """
        Parameters:
            account: Azure account.
            container: ABS container name.
            sas_token: Shared-Access Signature token. Token should be specified
                without a leading '?'.
            storage_endpoint_suffix: Deliver order to a sovereign cloud.
            path_prefix: Custom string to prepend to the files delivered to the
                bucket. A slash (/) character will be treated as a "folder".
                Any other characters will be added as a prefix to the files.
            archive_type: Archive order files. Only supports 'zip'.
            single_archive: Archive all bundles together in a single file.
            archive_filename: Custom naming convention to use to name the
                archive file that is received. Uses the template variables
                {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        """
        self.account = account
        self.container = container
        self.sas_token = sas_token
        self.storage_endpoint_suffix = storage_endpoint_suffix
        self.path_prefix = path_prefix

        super().__init__(archive_type, single_archive, archive_filename)

    @classmethod
    def from_dict(cls, details: dict) -> AzureBlobStorageDelivery:
        """Create AzureBlobStorageDelivery instance from Orders API spec
        representation.

        Parameters:
            details: API spec representation of delivery.

        Returns:
            AzureBlobStorageDelivery instance
        """
        cloud_details = _get_cloud_details(details, cls.cloud_key)
        return cls(**cloud_details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of AzureBlobStorageDelivery.
        """
        cloud_details = {
            'account': self.account,
            'container': self.container,
            'sas_token': self.sas_token,
        }

        if self.storage_endpoint_suffix:
            cloud_details['storage_endpoint_suffix'] = \
                self.storage_endpoint_suffix

        if self.path_prefix:
            cloud_details['path_prefix'] = self.path_prefix

        details = super().to_dict()
        details[self.cloud_key] = cloud_details
        return details


class GoogleCloudStorageDelivery(Delivery):
    '''Google Cloud Storage delivery description for an order detail.'''
    cloud_key = 'google_cloud_storage'

    def __init__(
        self,
        bucket: str,
        credentials: str,
        path_prefix: str = None,
        archive_type: str = False,
        single_archive: bool = False,
        archive_filename: str = None
    ):
        """
        Parameters:
            bucket: GCS bucket name.
            credentials: JSON-string of service account for bucket.
            path_prefix: Custom string to prepend to the files delivered to the
                bucket. A slash (/) character will be treated as a "folder".
                Any other characters will be added as a prefix to the files.
            archive_type: Archive order files. Only supports 'zip'.
            single_archive: Archive all bundles together in a single file.
            archive_filename: Custom naming convention to use to name the
                archive file that is received. Uses the template variables
                {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        """
        self.bucket = bucket
        self.credentials = credentials
        self.path_prefix = path_prefix
        super().__init__(archive_type, single_archive, archive_filename)

    @classmethod
    def from_dict(cls, details: dict) -> GoogleCloudStorageDelivery:
        """Create GoogleCloudStorageDelivery instance from Orders API spec
        representation.

        Parameters:
            details: API spec representation of delivery.

        Returns:
            GoogleCloudStorageDelivery instance
        """
        cloud_details = _get_cloud_details(details, cls.cloud_key)
        return cls(**cloud_details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of GoogleCloudStorageDelivery.
        """
        cloud_details = {
            'bucket': self.bucket,
            'credentials': self.credentials,
        }

        if self.path_prefix:
            cloud_details['path_prefix'] = self.path_prefix

        details = super().to_dict()
        details[self.cloud_key] = cloud_details
        return details


class GoogleEarthEngineDelivery(Delivery):
    '''Google Earth Engine delivery description for an order detail.'''
    cloud_key = 'google_earth_engine'

    def __init__(
        self,
        project: str,
        collection: str,
        archive_type: str = False,
        single_archive: bool = False,
        archive_filename: str = None
    ):
        """
        Parameters:
            project: GEE project name.
            collection: GEE Image Collection name.
            archive_type: Archive order files. Only supports 'zip'.
            single_archive: Archive all bundles together in a single file.
            archive_filename: Custom naming convention to use to name the
                archive file that is received. Uses the template variables
                {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        """
        self.project = project
        self.collection = collection
        super().__init__(archive_type, single_archive, archive_filename)

    @classmethod
    def from_dict(cls, details: dict) -> GoogleEarthEngineDelivery:
        """Create GoogleEarthEngineDelivery instance from Orders API spec
        representation.

        Parameters:
            details: API spec representation of delivery.

        Returns:
            GoogleEarthEngineDelivery instance
        """
        cloud_details = _get_cloud_details(details, cls.cloud_key)
        return cls(**cloud_details)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of GoogleEarthEngineDelivery.
        """
        cloud_details = {
            'project': self.project,
            'collection': self.collection,
        }

        details = super().to_dict()
        details[self.cloud_key] = cloud_details
        return details


class ToolException(Exception):
    '''Exceptions thrown by Tool'''
    pass


class Tool():
    '''Tool description for an order detail.

    See [Tools and Toolchains](
    https://developers.planet.com/docs/orders/tools-toolchains/)
    for more information on available tools and tool parameters.
    '''
    def __init__(
        self,
        name: str,
        parameters: dict
    ):
        """
        Parameters:
            name: Tool name.
            parameters: Tool parameters.
        """
        self.name = specs.validate_tool(name)
        self.parameters = parameters

    def __eq__(self, other):
        return (self.name == other.name and
                self.parameters == other.parameters)

    @classmethod
    def from_dict(cls, details: dict) -> Tool:
        """Create Tool instance from Orders API spec representation.

        Parameters:
            details: API spec representation of Tool.

        Returns:
            Tool instance
        """
        if len(details) != 1:
            raise ToolException(
                'Tool description must have only one item, name: parameters')
        name, parameters = details.popitem()
        return cls(name, parameters)

    def to_dict(self) -> dict:
        """Get Orders API spec representation.

        Returns:
            API spec representation of Tool.
        """
        return {self.name: self.parameters}


class ClipTool(Tool):
    '''Clip tool description for a given clip region.'''
    def __init__(
        self,
        aoi: Union[dict, geojson.Polygon]
    ):
        """
        Parameters:
            aoi: clip GeoJSON.
        """
        if not isinstance(aoi, geojson.Polygon):
            try:
                aoi = geojson.Polygon.from_geometry(aoi)
            except AttributeError:
                aoi = geojson.Polygon(aoi)

        parameters = {'aoi': aoi.to_dict()}
        super().__init__('clip', parameters)
