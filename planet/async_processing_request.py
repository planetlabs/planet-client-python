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
"""Functionality for preparing Async Processing API requests.

A request has three parts: `input` (where and what data), `output` (size,
formats and delivery bucket) and an evalscript (how to process the data).

Example:
    ```python
    from planet import async_processing_request as apr

    request = apr.build_request(
        input=apr.process_input(
            data=[apr.data_source('sentinel-2-l2a',
                                  time_from='2022-06-20T00:00:00Z',
                                  time_to='2022-06-30T23:59:59Z')],
            bbox=[426000, 3960000, 462000, 3994000],
            crs='http://www.opengis.net/def/crs/EPSG/0/32633'),
        output=apr.process_output(
            delivery=apr.s3_bucket('s3://my-bucket/ndvi',
                                   iam_role_arn='arn:aws:iam::1:role/sh'),
            resx=10,
            resy=10),
        evalscript=open('ndvi.js').read())
    ```
"""
from typing import Any, Dict, List, Optional

from planet.exceptions import ClientError


def build_request(input: dict,
                  output: dict,
                  evalscript: Optional[str] = None,
                  evalscript_reference: Optional[dict] = None) -> dict:
    """Prepare an Async Processing API request.

    Exactly one of `evalscript` and `evalscript_reference` must be given.

    Parameters:
        input: Bounds and data sources. See
            [planet.async_processing_request.process_input][].
        output: Output size, responses and delivery. See
            [planet.async_processing_request.process_output][].
        evalscript: The evalscript source.
        evalscript_reference: Location of a stored evalscript. See
            [planet.async_processing_request.s3_bucket][] and
            [planet.async_processing_request.gs_bucket][].

    Returns:
        dict: the request body.

    Raises:
        planet.exceptions.ClientError: If neither or both evalscript
            options are given.
    """
    if (evalscript is None) == (evalscript_reference is None):
        raise ClientError(
            'Exactly one of evalscript and evalscript_reference is required.')

    request: Dict[str, Any] = {'input': input, 'output': output}
    if evalscript is not None:
        request['evalscript'] = evalscript
    else:
        request['evalscriptReference'] = evalscript_reference
    return request


def process_input(data: List[dict],
                  bbox: Optional[List[float]] = None,
                  geometry: Optional[dict] = None,
                  crs: Optional[str] = None) -> dict:
    """Prepare the `input` part of a request.

    Give `bbox`, `geometry` or both. With both, the image covers the bbox and
    data is rendered only inside the geometry.

    Parameters:
        data: Data sources. See
            [planet.async_processing_request.data_source][].
        bbox: `[minx, miny, maxx, maxy]` in `crs`.
        geometry: GeoJSON geometry in `crs`.
        crs: CRS URI of `bbox` and `geometry`, e.g.
            `http://www.opengis.net/def/crs/EPSG/0/32633`. The server
            defaults to WGS84 (CRS84).

    Raises:
        planet.exceptions.ClientError: If neither bbox nor geometry is given,
            bbox does not have four values, or data is empty.
    """
    if bbox is None and geometry is None:
        raise ClientError('One or both of bbox and geometry is required.')
    if bbox is not None and len(bbox) != 4:
        raise ClientError('bbox must have four values: minx,miny,maxx,maxy.')
    if not data:
        raise ClientError('At least one data source is required.')

    bounds: Dict[str, Any] = {}
    if bbox is not None:
        bounds['bbox'] = list(bbox)
    if geometry is not None:
        bounds['geometry'] = geometry
    if crs is not None:
        bounds['properties'] = {'crs': crs}
    return {'bounds': bounds, 'data': list(data)}


def data_source(type: str,
                time_from: Optional[str] = None,
                time_to: Optional[str] = None,
                max_cloud_coverage: Optional[float] = None,
                mosaicking_order: Optional[str] = None,
                id: Optional[str] = None,
                processing: Optional[dict] = None) -> dict:
    """Prepare one entry of `input.data`.

    Parameters:
        type: Data collection type, e.g. `sentinel-2-l2a`, or `byoc-<id>`
            for a collection you own.
        time_from: Start of the time range, ISO 8601, e.g.
            `2022-06-20T00:00:00Z`.
        time_to: End of the time range, ISO 8601.
        max_cloud_coverage: Maximum scene cloud cover, 0 to 100.
        mosaicking_order: `mostRecent`, `leastRecent` or `leastCC`.
        id: Identifier used to reference this source in the evalscript when
            the request fuses several sources.
        processing: Extra processing options, e.g.
            `{'upsampling': 'BICUBIC'}`.
    """
    source: Dict[str, Any] = {'type': type}
    if id is not None:
        source['id'] = id

    data_filter: Dict[str, Any] = {}
    if time_from is not None or time_to is not None:
        time_range = {}
        if time_from is not None:
            time_range['from'] = time_from
        if time_to is not None:
            time_range['to'] = time_to
        data_filter['timeRange'] = time_range
    if max_cloud_coverage is not None:
        data_filter['maxCloudCoverage'] = max_cloud_coverage
    if mosaicking_order is not None:
        data_filter['mosaickingOrder'] = mosaicking_order
    if data_filter:
        source['dataFilter'] = data_filter

    if processing:
        source['processing'] = processing
    return source


def process_output(delivery: dict,
                   width: Optional[int] = None,
                   height: Optional[int] = None,
                   resx: Optional[float] = None,
                   resy: Optional[float] = None,
                   responses: Optional[List[dict]] = None) -> dict:
    """Prepare the `output` part of a request.

    Give `width` and `height` in pixels, or `resx` and `resy` in CRS units,
    not both. Each dimension may be at most 10000 pixels.

    Parameters:
        delivery: Destination bucket. See
            [planet.async_processing_request.s3_bucket][] and
            [planet.async_processing_request.gs_bucket][].
        width: Image width in pixels.
        height: Image height in pixels.
        resx: Horizontal resolution in CRS units.
        resy: Vertical resolution in CRS units.
        responses: Output files. See
            [planet.async_processing_request.response][]. The server defaults
            to one PNG named `default`.

    Raises:
        planet.exceptions.ClientError: If size and resolution are both given,
            or either is given incompletely.
    """
    size = (width, height)
    res = (resx, resy)
    if None not in size and None not in res:
        raise ClientError('Give width/height or resx/resy, not both.')
    for pair, names in ((size, 'width and height'), (res, 'resx and resy')):
        if (pair[0] is None) != (pair[1] is None):
            raise ClientError(f'{names} must be given together.')

    output: Dict[str, Any] = {}
    if width is not None:
        output['width'] = width
        output['height'] = height
    if resx is not None:
        output['resx'] = resx
        output['resy'] = resy
    if responses:
        output['responses'] = list(responses)
    output['delivery'] = delivery
    return output


def response(identifier: str = 'default',
             format_type: str = 'image/tiff') -> dict:
    """Prepare one entry of `output.responses`.

    Parameters:
        identifier: Must match an output `id` in the evalscript's `setup()`,
            or be `userdata`.
        format_type: `image/tiff`, `image/png`, `image/jpeg` or
            `application/json`.
    """
    return {'identifier': identifier, 'format': {'type': format_type}}


def s3_bucket(url: str,
              iam_role_arn: Optional[str] = None,
              access_key: Optional[str] = None,
              secret_access_key: Optional[str] = None,
              region: Optional[str] = None) -> dict:
    """Amazon S3 location, for delivery or an evalscript reference.

    Give `iam_role_arn` (recommended) or `access_key` and
    `secret_access_key`.

    For delivery, results go to `<url>/<REQUEST_ID>/<OUTPUT>` unless `url`
    contains the `<REQUEST_ID>` or `<OUTPUT>` placeholders.

    Parameters:
        url: `s3://bucket/prefix`.
        iam_role_arn: Role the service assumes to access the bucket.
        access_key: AWS access key ID.
        secret_access_key: AWS secret access key.
        region: Bucket region, if it differs from the deployment's region.

    Raises:
        planet.exceptions.ClientError: If url is not an s3:// URL or
            credentials are missing or incomplete.
    """
    if not url.startswith('s3://'):
        raise ClientError(f'S3 url must start with s3://; got {url!r}.')
    has_keys = access_key is not None or secret_access_key is not None
    if iam_role_arn is None and not has_keys:
        raise ClientError('S3 access requires iam_role_arn or access_key and '
                          'secret_access_key.')
    if has_keys and (access_key is None or secret_access_key is None):
        raise ClientError(
            'access_key and secret_access_key must be given together.')

    info = {'url': url}
    if iam_role_arn is not None:
        info['iamRoleARN'] = iam_role_arn
    if access_key is not None and secret_access_key is not None:
        info['accessKey'] = access_key
        info['secretAccessKey'] = secret_access_key
    if region is not None:
        info['region'] = region
    return {'s3': info}


def gs_bucket(url: str, credentials: str) -> dict:
    """Google Cloud Storage location, for delivery or an evalscript
    reference.

    Parameters:
        url: `gs://bucket/prefix`.
        credentials: Base64-encoded service account key JSON. The account
            needs read and write access to the bucket, e.g.
            `roles/storage.objectAdmin`. `roles/storage.objectCreator` is
            not enough.

    Raises:
        planet.exceptions.ClientError: If url is not a gs:// URL.
    """
    if not url.startswith('gs://'):
        raise ClientError(f'GCS url must start with gs://; got {url!r}.')
    return {'gs': {'url': url, 'credentials': credentials}}
