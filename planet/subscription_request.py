# Copyright 2023 Planet Labs PBC.
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
"""Functionality for preparing subscription requests."""
from datetime import datetime
from typing import Any, Dict, Optional, List

from . import geojson, specs
from .exceptions import ClientError

NOTIFICATIONS_TOPICS = ('delivery.success',
                        'delivery.match',
                        'delivery.failed',
                        'status.backfill.completed',
                        'status.completed',
                        'status.cancelled',
                        'status.pending',
                        'status.all',
                        'status.suspended',
                        'status.failed')

REPROJECT_KERNEL = ('near',
                    'bilinear',
                    'cubic',
                    'cubicspline',
                    'lanczos',
                    'average',
                    'mode',
                    'min',
                    'max',
                    'med',
                    'q1',
                    'q3')
REPROJECT_KERNEL_DEFAULT = 'near'


def build_request(name: str,
                  source: dict,
                  delivery: dict,
                  notifications: Optional[dict] = None,
                  tools: Optional[List[dict]] = None) -> dict:
    """Prepare a subscriptions request.


    ```python
    >>> from datetime import datetime
    >>> from planet.subscription_request import (
    ...     build_request, catalog_source, amazon_s3)
    ...
    ... geom = {
    ...     "coordinates": [[[139.5648193359375,35.42374884923695],
    ...                     [140.1031494140625,35.42374884923695],
    ...                     [140.1031494140625,35.77102915686019],
    ...                     [139.5648193359375,35.77102915686019],
    ...                     [139.5648193359375,35.42374884923695]]],
    ...     "type": "Polygon"
    ... }
    >>> source = catalog_source(
    ...     ["PSScene"], ["ortho_analytic_4b"], geom, datetime(2021,3,1))

    >>> delivery = amazon_s3(
    ...     ACCESS_KEY_ID, SECRET_ACCESS_KEY, "test", "us-east-1")
    ...
    >>> subscription_request = build_request(
    ...     'test_subscription', source, delivery)
    ...

    ```

    Parameters:
        name: Name of the subscription.
        source: A source for the subscription, i.e. catalog.
        delivery: A delivery mechanism e.g. GCS, AWS, Azure, or OCS.
        notifications: Specify notifications via email/webhook.
        tools: Tools to apply to the products. Order defines
            the toolchain order of operatations.
    """
    details = {"name": name, "source": source, "delivery": delivery}

    if notifications:
        details['notifications'] = notifications

    if tools:
        details['tools'] = tools

    return details


def catalog_source(
    item_types: List[str],
    asset_types: List[str],
    geometry: dict,
    start_time: datetime,
    filter: Optional[dict] = None,
    end_time: Optional[datetime] = None,
    rrule: Optional[str] = None,
) -> dict:
    '''Catalog subscription source.

    Parameters:
    item_types: The class of spacecraft and processing level of the
        subscription's matching items, e.g. PSScene.
    asset_types: The data products which will be delivered for all subscription
        matching items. An item will only match and deliver if all specified
        asset types are published for that item.
    geometry: The area of interest of the subscription that will be used to
        determine matches.
    start_time: The start time of the subscription. This time can be in the
        past or future.
    filter: The filter criteria based on item-level metadata.
    end_time: The end time of the subscription. This time can be in the past or
        future, and must be after the start_time.
    rrule: The recurrence rule, given in iCalendar RFC 5545 format. Only
        monthly recurrences are supported at this time.

    Raises:
        planet.exceptions.ClientError: If start_time or end_time are not valid
            datetimes
    '''
    try:
        asset_types = [
            specs.validate_asset_type(item_types, asset_type)
            for asset_type in asset_types
        ]
    except specs.SpecificationException as exception:
        raise ClientError(exception)

    parameters = {
        "item_types": item_types,
        "asset_types": asset_types,
        "geometry": geojson.as_geom(geometry),
    }

    try:
        parameters['start_time'] = _datetime_to_rfc3339(start_time)
    except AttributeError:
        raise ClientError('Could not convert start_time to an iso string')

    if filter:
        parameters['filter'] = filter

    if end_time:
        try:
            parameters['end_time'] = _datetime_to_rfc3339(end_time)
        except AttributeError:
            raise ClientError('Could not convert end_time to an iso string')

    if rrule:
        parameters['rrule'] = rrule

    return {"type": "catalog", "parameters": parameters}


def _datetime_to_rfc3339(value: datetime) -> str:
    """Converts the datetime to an RFC3339 string"""
    iso = value.isoformat()
    if not value.utcoffset():
        # rfc3339 needs a Z if there is no timezone offset
        iso += 'Z'
    return iso


def _delivery(type: str, parameters: dict) -> dict:
    return {"type": type, "parameters": parameters}


def amazon_s3(aws_access_key_id: str,
              aws_secret_access_key: str,
              bucket: str,
              aws_region: str) -> dict:
    '''Delivery to Amazon S3.

    Parameters:
        aws_access_key_id: S3 account access key.
        aws_secret_access_key: S3 account secret key.
        bucket: The name of the bucket that will receive the order output.
        aws_region: The region where the bucket lives in AWS.
    '''
    parameters = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'bucket': bucket,
        'aws_region': aws_region,
    }

    return _delivery('amazon_s3', parameters)


def azure_blob_storage(account: str,
                       container: str,
                       sas_token: str,
                       storage_endpoint_suffix: Optional[str] = None) -> dict:
    '''Delivery to Azure Blob Storage.

    Parameters:
        account: Azure account.
        container: ABS container name.
        sas_token: Shared-Access Signature token. Token should be specified
            without a leading '?'.
        storage_endpoint_suffix: Deliver order to a sovereign cloud. The
            default is "core.windows.net".
    '''
    parameters = {
        'account': account,
        'container': container,
        'sas_token': sas_token,
    }

    if storage_endpoint_suffix:
        parameters['storage_endpoint_suffix'] = storage_endpoint_suffix

    return _delivery('azure_blob_storage', parameters)


def google_cloud_storage(credentials: str, bucket: str) -> dict:
    '''Delivery to Google Cloud Storage.

    Parameters:
        credentials: JSON-string of service account for bucket.
        bucket: GCS bucket name.
    '''
    parameters = {
        'bucket': bucket,
        'credentials': credentials,
    }

    return _delivery('google_cloud_storage', parameters)


def oracle_cloud_storage(customer_access_key_id: str,
                         customer_secret_key: str,
                         bucket: str,
                         region: str,
                         namespace: str) -> dict:
    '''Delivery to Oracle Cloud Storage.

    Parameters:
        customer_access_key_id: Customer Secret Key credentials.
        customer_secret_key: Customer Secret Key credentials.
        bucket: The name of the bucket that will receive the order output.
        region: The region where the bucket lives in Oracle.
        namespace: Object Storage namespace name.
    '''
    parameters = {
        'customer_access_key_id': customer_access_key_id,
        'customer_secret_key': customer_secret_key,
        'bucket': bucket,
        'region': region,
        'namespace': namespace
    }

    return _delivery('oracle_cloud_storage', parameters)


def notifications(url: str, topics: List[str]) -> dict:
    '''Specify a subscriptions API notification.

    Webhook notifications proactively notify you when a subscription matches
    and delivers an item so you have confidence that you have all the expected
    imagery.

    Parameters:
        url: location of webhook/callback where you expect to receive updates.
        topics: Event types that you can choose to be notified about.
    '''
    for i, t in enumerate(topics):
        try:
            topics[i] = specs.get_match(t, NOTIFICATIONS_TOPICS, 'topic')
        except specs.SpecificationException as e:
            raise ClientError(e)

    return {"webhook": {"url": url, "topics": topics}}


def _tool(type: str, parameters: dict) -> dict:
    return {"type": type, "parameters": parameters}


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
    '''Specify a subscriptions API band math tool.

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
    '''  # noqa
    try:
        pixel_type = specs.get_match(pixel_type,
                                     specs.BAND_MATH_PIXEL_TYPE,
                                     'pixel_type')
    except specs.SpecificationException as e:
        raise ClientError(e)

    # e.g. {"b1": "b1", "b2":"arctan(b1)"} if b1 and b2 are specified
    parameters = dict((k, v) for k, v in locals().items() if v)
    return _tool('bandmath', parameters)


def clip_tool(aoi: dict) -> dict:
    '''Specify a subscriptions API clip tool.

    Imagery and udm files will be clipped to your area of interest. nodata
    pixels will be preserved. Xml file attributes “filename”, “numRows”,
    “numColumns” and “footprint” will be updated based on the clip results.

    The clipped output files will have “_clip” appended to their file names. If
    the clip aoi is so large that full scenes may be delivered without any
    clipping, those files will not have “_clip” appended to their file name.

    Parameters:
        aoi: GeoJSON polygon or multipolygon defining the clip area, with up to
            500 vertices. The minimum geographic area of any polygon or
            internal ring is one square meter.

    Raises:
        planet.exceptions.ClientError: If aoi is not a valid polygon or
            multipolygon.
    '''
    valid_types = ['Polygon', 'MultiPolygon']

    geom = geojson.as_geom(aoi)
    if geom['type'].lower() not in [v.lower() for v in valid_types]:
        raise ClientError(
            f'Invalid geometry type: {geom["type"]} is not in {valid_types}.')

    return _tool('clip', {'aoi': aoi})


def file_format_tool(file_format: str) -> dict:
    '''Specify a subscriptions API file format tool.

    Parameters:
        file_format: The format of the tool output. Either "COG" or "PL_NITF".

    Raises:
        planet.exceptions.ClientError: If file_format is not valid.
    '''
    try:
        file_format = specs.validate_file_format(file_format)
    except specs.SpecificationException as e:
        raise ClientError(e)

    return _tool('file_format', {'format': file_format})


def harmonize_tool(target_sensor: str) -> dict:
    '''Specify a subscriptions API harmonize tool.

    Each sensor value transforms items captured by a defined set of instrument
    IDs. Items which have not been captured by that defined set of instrument
    IDs are unaffected by (passed through) the harmonization operation.

    Parameters:
        target_sensor: A value indicating to what sensor the input asset types
            should be calibrated.

    Raises:
        planet.exceptions.ClientError: If target_sensor is not valid.
    '''
    try:
        target_sensor = specs.get_match(target_sensor,
                                        specs.HARMONIZE_TOOL_TARGET_SENSORS,
                                        'target_sensor')
    except specs.SpecificationException as e:
        raise ClientError(e)

    return _tool('harmonize', {'target_sensor': target_sensor})


def reproject_tool(projection: str,
                   resolution: Optional[float] = None,
                   kernel: str = REPROJECT_KERNEL_DEFAULT) -> dict:
    '''Specify a subscriptions API reproject tool.

    Parameters:
        projection: A coordinate system in the form EPSG:n (for example,
            EPSG:4326 for WGS84, EPSG:32611 for UTM 11 North (WGS84), or
            EPSG:3857 for Web Mercator). Well known text CRS values are also
            supported (for example, WGS84).
        resolution: The pixel width and height in the output file. If not
            provided, the default is the resolution of the input item. This
            value is in meters unless the coordinate system is geographic (such
            as EPSG:4326), in which case, it is pixel size in decimal degrees.
        kernel: The resampling kernel used. UDM files always use "near".

    Raises:
        planet.exceptions.ClientError: If kernel is not valid.
    '''
    try:
        kernel = specs.get_match(kernel, REPROJECT_KERNEL, 'kernel')
    except specs.SpecificationException as e:
        raise ClientError(e)

    parameters: Dict[str, Any] = {"projection": projection, "kernel": kernel}
    if resolution is not None:
        parameters['resolution'] = resolution

    return _tool('reproject', parameters)


def toar_tool(scale_factor: int = 10000) -> dict:
    '''Specify a subscriptions API reproject tool.

    The toar tool supports the analytic asset type for PSScene, PSOrthoTile,
    and REOrthoTile item types. In addition to the analytic asset, the
    corresponding XML metadata asset type is required.

    Parameters:
        scale_factor: Scale factor applied to convert 0.0 to 1.0 reflectance
            floating point values to a value that fits in 16bit integer pixels.
            The API default is 10000. Values over 65535 could result in high
            reflectances not fitting in 16bit integers.
    '''
    return _tool('toar', {'scale_factor': scale_factor})
