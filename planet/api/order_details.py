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
import logging
from typing import List

from .. import geojson, specs

LOGGER = logging.getLogger(__name__)


class OrderDetailsException(Exception):
    """Exceptions thrown by OrderDetails"""
    pass


def build_request(
        name: str,
        products: List[dict],
        subscription_id: int = 0,
        delivery: dict = None,
        notifications: dict = None,
        order_type: str = None,
        tools: List[dict] = None
) -> dict:
    '''Prepare an order request.

    ```python
    >>> from planet.api.order_details import build_request, product
    >>>
    >>> image_ids = ['3949357_1454705_2020-12-01_241c']
    >>> order_request = build_request(
    ...     'test_order',
    ...     [product(image_ids, 'analytic', 'psorthotile')]
    ... )
    ...

    ```

    Parameters:
        name: Name of the order.
        products: Product(s) from the Data API to order.
        subscription_id: Apply this orders against this quota subscription.
        delivery: Specify custom delivery handling.
        notifications: Specify custom notifications handling.
        order_type: Accept a partial order, indicated by 'partial'.
        tools: Tools to apply to the products. Order defines
            the toolchain order of operatations.

    '''
    details = {
        'name': name,
        'products': products
    }

    if subscription_id:
        details['subscription_id'] = subscription_id

    if delivery:
        details['delivery'] = delivery

    if notifications:
        details['notifications'] = notifications

    if order_type:
        order_type = specs.validate_order_type(order_type)
        details['order_type'] = order_type

    if tools:
        details['tools'] = tools

    return details


def product(
    item_ids: List[str],
    product_bundle: str,
    item_type: str,
    fallback_bundle: str = None
) -> dict:
    '''Product description for an order detail.

    Parameters:
        item_ids: IDs of the catalog items to include in the order.
        product_bundle: Set of asset types for the catalog items.
        item_type: The class of spacecraft and processing characteristics
            for the catalog items.
        fallback_bundle: In case product_bundle not having
            all asset types available, which would result in failed
            delivery, try a fallback bundle
    '''
    product_bundle = specs.validate_bundle(product_bundle)
    item_type = specs.validate_item_type(item_type, product_bundle)

    if fallback_bundle is not None:
        fallback_bundle = specs.validate_bundle(fallback_bundle)
        specs.validate_item_type(item_type, fallback_bundle)
        product_bundle = ','.join([product_bundle, fallback_bundle])

    product_dict = {
        'item_ids': item_ids,
        'item_type': item_type,
        'product_bundle': product_bundle
    }
    return product_dict


def notifications(
    email: bool = False,
    webhook_url: str = None,
    webhook_per_order: bool = False
) -> dict:
    '''Notifications description for an order detail.

    Parameters:
        email: Enable email notifications for an order.
        webhook_url: URL for notification when the order is ready.
        webhook_per_order: Request a single webhook call per order instead
            of one call per each delivered item.
    '''
    details = {}

    if email:
        details['email'] = email

    if webhook_url is not None:
        details['webhook_url'] = webhook_url

    if webhook_per_order:
        details['webhook_per_order'] = True

    return details


def delivery(
    archive_type: str = None,
    single_archive: bool = False,
    archive_filename: str = None,
    cloud_config: dict = None
) -> dict:
    '''Order delivery configuration.

    Example:
        ```python
        amazon_s3_config = amazon_s3(
            'access_key',
            'secret_access_key',
            'bucket_name',
            'us-east-2',
            'folder1/prefix/'
        )
        delivery_config = delivery(
            archive_type='zip',
            single_archive=True,
            archive_filename='{{order_id}}.zip'
            cloud_config=amazon_s3_config
        )
        ```

    Parameters:
        archive_type: Archive order files. Only supports 'zip'.
        single_archive: Archive all bundles together in a single file.
        archive_filename: Custom naming convention to use to name the
            archive file that is received. Uses the template variables
            {{name}} and {{order_id}}. e.g. "{{name}}_{{order_id}}.zip".
        cloud_config: Cloud delivery configuration.
    '''
    if archive_type:
        archive_type = specs.validate_archive_type(archive_type)

    fields = ['archive_type', 'single_archive', 'archive_filename']
    values = [archive_type, single_archive, archive_filename]

    config = dict((k, v) for k, v in zip(fields, values) if v)

    if cloud_config:
        config.update(cloud_config)
    return config


def amazon_s3(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    bucket: str,
    aws_region: str,
    path_prefix: str = None
) -> dict:
    '''Amazon S3 Cloud configuration.

    Parameters:
        aws_access_key_id: S3 account access key.
        aws_secret_access_key: S3 account secret key.
        bucket: The name of the bucket that will receive the order output.
        aws_region: The region where the bucket lives in AWS.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    '''
    cloud_details = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'bucket': bucket,
        'aws_region': aws_region,
    }

    if path_prefix:
        cloud_details['path_prefix'] = path_prefix

    return {'amazon_s3': cloud_details}


def azure_blob_storage(
    account: str,
    container: str,
    sas_token: str,
    storage_endpoint_suffix: str = None,
    path_prefix: str = None
) -> dict:
    '''Azure Blob Storage configuration.

    Parameters:
        account: Azure account.
        container: ABS container name.
        sas_token: Shared-Access Signature token. Token should be specified
            without a leading '?'.
        storage_endpoint_suffix: Deliver order to a sovereign cloud.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    '''
    cloud_details = {
        'account': account,
        'container': container,
        'sas_token': sas_token,
    }

    if storage_endpoint_suffix:
        cloud_details['storage_endpoint_suffix'] = storage_endpoint_suffix

    if path_prefix:
        cloud_details['path_prefix'] = path_prefix

    return {'azure_blob_storage': cloud_details}


def google_cloud_storage(
    bucket: str,
    credentials: str,
    path_prefix: str = None
) -> dict:
    '''Google Cloud Storage configuration.

    Parameters:
        bucket: GCS bucket name.
        credentials: JSON-string of service account for bucket.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    '''
    cloud_details = {
        'bucket': bucket,
        'credentials': credentials,
    }

    if path_prefix:
        cloud_details['path_prefix'] = path_prefix

    return {'google_cloud_storage': cloud_details}


def google_earth_engine(
    project: str,
    collection: str
) -> dict:
    '''Google Earth Engine configuration.

    Parameters:
        project: GEE project name.
        collection: GEE Image Collection name.
    '''
    cloud_details = {
        'project': project,
        'collection': collection,
    }
    return {'google_earth_engine': cloud_details}


def tool(name: str, parameters: dict) -> dict:
    '''Create the API spec representation of a tool.

    See [Tools and Toolchains](
    https://developers.planet.com/docs/orders/tools-toolchains/)
    for more information on available tools and tool parameters.

    Parameters:
        name: Tool name.
        parameters: Tool parameters.
    '''
    name = specs.validate_tool(name)
    return {name: parameters}


def clip_tool(aoi: dict) -> dict:
    '''Create the API spec representation of a clip tool.

    Example:
        ```python
        aoi = {
            "type": "Polygon",
            "coordinates": [[
                [37.791595458984375, 14.84923123791421],
                [37.90214538574219, 14.84923123791421],
                [37.90214538574219, 14.945448293647944],
                [37.791595458984375, 14.945448293647944],
                [37.791595458984375, 14.84923123791421]
            ]]
          }
        tool = clip_tool(aoi)
        ```

    Parameters:
        aoi: clip GeoJSON.

    Raises:
        geojson.GeoJSONException: If GeoJSON is not a valid polygon.
    '''
    parameters = {'aoi': geojson.as_polygon(aoi)}
    return tool('clip', parameters)
