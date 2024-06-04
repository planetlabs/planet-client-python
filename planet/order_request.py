# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
from typing import Any, Dict, List, Mapping, Optional, Union

from . import geojson, specs
from .exceptions import ClientError

LOGGER = logging.getLogger(__name__)


def build_request(name: str,
                  products: List[dict],
                  subscription_id: int = 0,
                  delivery: Optional[dict] = None,
                  notifications: Optional[dict] = None,
                  order_type: Optional[str] = None,
                  tools: Optional[List[dict]] = None,
                  stac: Optional[dict] = None,
                  hosting: Optional[str] = None,
                  collection_id: Optional[str] = None) -> dict:
    """Prepare an order request.

    ```python
    >>> from planet.order_request import (
    ...     build_request, product, toar_tool, reproject_tool, tile_tool)
    ...
    >>> products = [
    ...     product(['20170614_113217_3163208_RapidEye-5'],
    ...             'analytic', 'REOrthoTile')])
    ... ]
    ...
    >>> tools = [
    ...     toar_tool(scale_factor=10000),
    ...     reproject_tool(projection='WSG84', kernel='cubic'),
    ...     tile_tool(1232, origin_x=-180, origin_y=-90,
    ...               pixel_size=0.000027056277056,
    ...               name_template='C1232_30_30_{tilex:04d}_{tiley:04d}')
    ... ]
    ...
    >>> order_request = build_request(
    ...     'test_order', products, tools)
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
        stac: Include STAC metadata.
        hosting: A hosting destination (e.g. Sentinel Hub).
        collection_id: A Sentinel Hub collection ID.

    Raises:
        planet.specs.SpecificationException: If order_type is not a valid
            order type.
    """
    details: Dict[str, Any] = {'name': name, 'products': products}

    if subscription_id:
        details['subscription_id'] = subscription_id

    if delivery:
        details['delivery'] = delivery

    if notifications:
        details['notifications'] = notifications

    if order_type:
        validated_order_type = specs.validate_order_type(order_type)
        details['order_type'] = validated_order_type

    if tools:
        details['tools'] = tools

    if stac:
        details['metadata'] = stac

    if hosting == 'sentinel_hub':
        details['hosting'] = sentinel_hub(collection_id)

    return details


def product(item_ids: List[str],
            product_bundle: str,
            item_type: str,
            fallback_bundle: Optional[str] = None) -> dict:
    """Product description for an order detail.

    Parameters:
        item_ids: IDs of the catalog items to include in the order.
        product_bundle: Set of asset types for the catalog items.
        item_type: The class of spacecraft and processing characteristics
            for the catalog items.
        fallback_bundle: In case product_bundle not having
            all asset types available, which would result in failed
            delivery, try a fallback bundle

    Raises:
        planet.specs.SpecificationException: If bundle or fallback bundle
            are not valid bundles or if item_type is not valid for the given
            bundle or fallback bundle.
    """
    item_type = specs.validate_item_type(item_type)
    validated_product_bundle = specs.validate_bundle(item_type, product_bundle)

    if fallback_bundle is not None:
        item_type = specs.validate_item_type(item_type)
        validated_fallback_bundle = specs.validate_bundle(
            item_type, fallback_bundle)
        validated_product_bundle = ','.join(
            [validated_product_bundle, validated_fallback_bundle])

    product_dict = {
        'item_ids': item_ids,
        'item_type': item_type,
        'product_bundle': validated_product_bundle
    }
    return product_dict


def notifications(email: Optional[bool] = None,
                  webhook_url: Optional[str] = None,
                  webhook_per_order: Optional[bool] = None) -> dict:
    """Notifications description for an order detail.

    Parameters:
        email: Enable email notifications for an order.
        webhook_url: URL for notification when the order is ready.
        webhook_per_order: Request a single webhook call per order instead
            of one call per each delivered item.
    """
    notifications_dict: Dict[str, Union[dict, bool]] = {}

    if webhook_url:
        webhook_dict: Dict[str, Union[str, bool]] = {
            'url': webhook_url,
        }
        if webhook_per_order is not None:
            wpo: bool = webhook_per_order
            webhook_dict['per_order'] = wpo

        notifications_dict['webhook'] = webhook_dict

    if email is not None:
        val: bool = email
        notifications_dict['email'] = val

    return notifications_dict


def delivery(archive_type: Optional[str] = None,
             single_archive: Optional[bool] = False,
             archive_filename: Optional[str] = None,
             cloud_config: Optional[Mapping] = None) -> dict:
    """Order delivery configuration.

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

    Raises:
        planet.specs.SpecificationException: If archive_type is not valid.
    """
    config: Dict[str, Any] = {}

    if archive_type:
        archive_type = specs.validate_archive_type(archive_type)

        if archive_filename is None:
            archive_filename = "{{name}}_{{order_id}}.zip"

        config.update(archive_type=archive_type,
                      archive_filename=archive_filename,
                      single_archive=single_archive)

    if cloud_config:
        config.update(cloud_config)

    return config


def amazon_s3(aws_access_key_id: str,
              aws_secret_access_key: str,
              bucket: str,
              aws_region: str,
              path_prefix: Optional[str] = None) -> dict:
    """Amazon S3 Cloud configuration.

    Parameters:
        aws_access_key_id: S3 account access key.
        aws_secret_access_key: S3 account secret key.
        bucket: The name of the bucket that will receive the order output.
        aws_region: The region where the bucket lives in AWS.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    """
    cloud_details = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'bucket': bucket,
        'aws_region': aws_region,
    }

    if path_prefix:
        cloud_details['path_prefix'] = path_prefix

    return {'amazon_s3': cloud_details}


def azure_blob_storage(account: str,
                       container: str,
                       sas_token: str,
                       storage_endpoint_suffix: Optional[str] = None,
                       path_prefix: Optional[str] = None) -> dict:
    """Azure Blob Storage configuration.

    Parameters:
        account: Azure account.
        container: ABS container name.
        sas_token: Shared-Access Signature token. Token should be specified
            without a leading '?'.
        storage_endpoint_suffix: Deliver order to a sovereign cloud.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    """
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


def google_cloud_storage(bucket: str,
                         credentials: str,
                         path_prefix: Optional[str] = None) -> dict:
    """Google Cloud Storage configuration.

    Parameters:
        bucket: GCS bucket name.
        credentials: JSON-string of service account for bucket.
        path_prefix: Custom string to prepend to the files delivered to the
            bucket. A slash (/) character will be treated as a "folder".
            Any other characters will be added as a prefix to the files.
    """
    cloud_details = {
        'bucket': bucket,
        'credentials': credentials,
    }

    if path_prefix:
        cloud_details['path_prefix'] = path_prefix

    return {'google_cloud_storage': cloud_details}


def google_earth_engine(project: str, collection: str) -> dict:
    """Google Earth Engine configuration.

    Parameters:
        project: GEE project name.
        collection: GEE Image Collection name.
    """
    cloud_details = {
        'project': project,
        'collection': collection,
    }
    return {'google_earth_engine': cloud_details}


def _tool(name: str, parameters: dict) -> dict:
    """Create the API spec representation of a tool.

    See [Tools and Toolchains](
    https://developers.planet.com/docs/orders/tools-toolchains/)
    for more information on available tools and tool parameters.

    Parameters:
        name: Tool name.
        parameters: Tool parameters.

    Raises:
        planet.specs.SpecificationException: If name is not the name of a valid
            Orders API tool.
    """
    name = specs.validate_tool(name)
    return {name: parameters}


def clip_tool(aoi: dict) -> dict:
    """Create the API spec representation of a clip tool.

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
        aoi: clip GeoJSON, either Polygon or Multipolygon.

    Raises:
        planet.exceptions.ClientError: If GeoJSON is not a valid polygon or
            multipolygon.
    """
    valid_types = ['Polygon', 'MultiPolygon', 'ref']

    geom = geojson.as_geom_or_ref(aoi)
    if geom['type'].lower() not in [v.lower() for v in valid_types]:
        raise ClientError(
            f'Invalid geometry type: {geom["type"]} is not in {valid_types}.')
    return _tool('clip', {'aoi': geom})


def composite_tool() -> dict:
    """Create the API spec representation of a composite tool.
    """
    return _tool('composite', {})


def coregister_tool(anchor_item: str) -> dict:
    """Create the API spec representation of a coregister tool.

    Parameters:
        anchor_item: The item_id of the item to which all other items should be
            coregistered.
    """
    return _tool('coregister', {'anchor_item': anchor_item})


def file_format_tool(file_format: str) -> dict:
    """Create the API spec representation of a file format tool.

    Parameters:
        file_format: The format of the tool output. Either 'COG' or 'PL_NITF'.

    Raises:
        planet.specs.SpecificationException: If file_format is not one of
            'COG' or 'PL_NITF'
    """
    file_format = specs.validate_file_format(file_format)
    return _tool('file_format', {'format': file_format})


def reproject_tool(projection: str,
                   resolution: Optional[float] = None,
                   kernel: Optional[str] = None) -> dict:
    """Create the API spec representation of a reproject tool.

    Parameters:
        projection: A coordinate system in the form EPSG:n. (ex. EPSG:4326 for
            WGS84, EPSG:32611 for UTM 11 North (WGS84), or EPSG:3857 for Web
            Mercator).
        resolution: The pixel width and height in the output file. The API
            default is the resolution of the input item. This value will be in
            meters unless the coordinate system is geographic (like EPSG:4326),
            then it will be a pixel size in decimal degrees.
        kernel: The resampling kernel used. The API default is "near". This
            parameter also supports "bilinear", "cubic", "cubicspline",
            "lanczos", "average" and "mode".
    """
    parameters = dict((k, v) for k, v in locals().items() if v)
    return _tool('reproject', parameters)


def tile_tool(tile_size: int,
              origin_x: Optional[float] = None,
              origin_y: Optional[float] = None,
              pixel_size: Optional[float] = None,
              name_template: Optional[str] = None,
              conformal_x_scaling: Optional[bool] = None) -> dict:
    """Create the API spec representation of a reproject tool.

    Parameters:
        tile_size: Height and width of output tiles in pixels and lines
            (always square).
        origin_x: Tiling system x origin in projected coordinates. The API
            default is zero.
        origin_y: Tiling system y origin in projected coordinates. The API
            default is zero.
        pixel_size: Tiling system pixel size in projected coordinates. The API
            default is the pixel_size of input raster.
        name_template: A naming template for creating output tile filenames.
            The API default is "{tilex}_{tiley}.tif" resulting in filenames
            like 128_200.tif. The {tilex} and {tiley} parameters can be of the
            form {tilex:06d} to produce a fixed width field with leading zeros.
    """
    parameters = dict((k, v) for k, v in locals().items() if v)
    return _tool('tile', parameters)


def toar_tool(scale_factor: Optional[int] = None) -> dict:
    """Create the API spec representation of a TOAR tool.

    Parameters:
        scale_factor: Scale factor applied to convert 0.0 to 1.0 reflectance
            floating point values to a value that fits in 16bit integer pixels.
            The API default is 10000. Values over 65535 could result in high
            reflectances not fitting in 16bit integers.
    """
    parameters = {}
    if scale_factor:
        parameters['scale_factor'] = scale_factor
    return _tool('toar', parameters)


def harmonize_tool(target_sensor: str) -> dict:
    """Create the API spec representation of a harmonize tool.

    Parameters:
        target_sensor: A value indicating to what sensor the input asset types
            should be calibrated.

    Raises:
        planet.exceptions.ClientError: If target_sensor is not valid.
    """

    try:
        target_sensor = specs.get_match(target_sensor,
                                        specs.HARMONIZE_TOOL_TARGET_SENSORS,
                                        'target_sensor')
    except specs.SpecificationException as e:
        raise ClientError(e)

    return _tool('harmonize', {'target_sensor': target_sensor})


def band_math_tool(b1: str,
                   b2: Optional[str] = None,
                   b3: Optional[str] = None,
                   b4: Optional[str] = None,
                   b5: Optional[str] = None,
                   b6: Optional[str] = None,
                   b7: Optional[str] = None,
                   b8: Optional[str] = None,
                   b9: Optional[str] = None,
                   b10: Optional[str] = None,
                   b11: Optional[str] = None,
                   b12: Optional[str] = None,
                   b13: Optional[str] = None,
                   b14: Optional[str] = None,
                   b15: Optional[str] = None,
                   pixel_type: str = specs.BAND_MATH_PIXEL_TYPE_DEFAULT):
    """Specify an Orders API band math tool.

    The parameters of the bandmath tool define how each output band in the
    derivative product should be produced, referencing the product inputs’
    original bands. Band math expressions may not reference neighboring pixels,
    as non-local operations are not supported. The tool can calculate up to 15
    bands for an item. Input band parameters may not be skipped. For example,
    if the b4 parameter is provided, then b1, b2, and b3 parameters are also
    required.

    For each band expression, the bandmath tool supports normal arithmetic
    operations and simple math operators offered in the Python numpy package.
    (For a list of supported mathematical functions, see
    [Bandmath supported numpy math routines](https://developers.planet.com/apis/orders/bandmath-numpy-routines/)).

    One bandmath imagery output file is produced for each product bundle, with
    output bands derived from the band math expressions. nodata pixels are
    processed with the band math equation. These files have “_bandmath”
    appended to their file names.

    The tool passes through UDM, RPC, and XML files, and does not update values
    in these files.

    Parameters:
        b1-b15: An expression defining how the output band should be computed.
        pixel_type: A value indicating what the output pixel type should be.

    Raises:
        planet.exceptions.ClientError: If pixel_type is not valid.
    """  # noqa
    try:
        pixel_type = specs.get_match(pixel_type,
                                     specs.BAND_MATH_PIXEL_TYPE,
                                     'pixel_type')
    except specs.SpecificationException as e:
        raise ClientError(e)

    # e.g. {"b1": "b1", "b2":"arctan(b1)"} if b1 and b2 are specified
    parameters = dict((k, v) for k, v in locals().items() if v)
    return _tool('bandmath', parameters)


def sentinel_hub(collection_id: Optional[str] = None) -> dict:
    """Specify a Sentinel Hub hosting destination."""
    params = {}
    if collection_id:
        params['collection_id'] = collection_id
    return {'sentinel_hub': params}
