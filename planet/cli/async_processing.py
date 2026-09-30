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
"""Async Processing API CLI"""
import base64
from contextlib import asynccontextmanager
from typing import List, Tuple

import click

from planet import async_processing_request as apr
from planet import exceptions, geojson
from planet.cli.io import echo_json
from planet.clients.async_processing import (DEFAULT_DEPLOYMENT,
                                             DEPLOYMENT_URLS,
                                             AsyncProcessingClient)

from .cmds import command
from .session import CliSession
from . import types

FORMATS = ['image/tiff', 'image/png', 'image/jpeg', 'application/json']

NOT_RUNNING = ('Request {} is not running. It has finished or does not '
               'exist. Check the delivery bucket for results or error.json.')


@asynccontextmanager
async def async_processing_client(ctx):
    async with CliSession(ctx) as sess:
        cl = AsyncProcessingClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group(name='async-processing')  # type: ignore
@click.pass_context
@click.option('--deployment',
              type=click.Choice(list(DEPLOYMENT_URLS)),
              default=DEFAULT_DEPLOYMENT,
              show_default=True,
              help='Deployment to send requests to. Input data must be '
              'hosted on the same deployment.')
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Async Processing API URL. '
              'Overrides --deployment.')
def async_processing(ctx, deployment, base_url):
    """Commands for the Async Processing API.

    Async Processing runs large Process API requests in the background and
    delivers results to an S3 or GCS bucket. Outputs may be up to 10000
    pixels in each dimension.

    Requires an OAuth2 login (`planet auth login`). Planet API keys are not
    accepted.

    Typical workflow:

    \b
    planet async-processing request --collection sentinel-2-l2a \\
        --bbox 12.44,41.87,12.54,41.93 --time-from 2024-06-01T00:00:00Z \\
        --time-to 2024-06-30T23:59:59Z --evalscript ndvi.js \\
        --width 2500 --height 2500 --delivery s3://my-bucket/ndvi \\
        --iam-role-arn arn:aws:iam::123456789012:role/planet > request.json
    planet async-processing create request.json
    planet async-processing wait <REQUEST_ID>
    """
    ctx.obj['BASE_URL'] = base_url or DEPLOYMENT_URLS[deployment]


def _parse_responses(values: Tuple[str, ...]) -> List[dict]:
    """Parse repeated `--response IDENTIFIER:FORMAT` options."""
    responses = []
    for value in values:
        identifier, sep, fmt = value.partition(':')
        if not sep or not identifier or fmt not in FORMATS:
            raise click.BadParameter(
                f'expected IDENTIFIER:FORMAT with FORMAT one of '
                f'{", ".join(FORMATS)}; got {value!r}.',
                param_hint='--response')
        responses.append(apr.response(identifier, fmt))
    return responses


def _bucket(url,
            iam_role_arn,
            access_key,
            secret_access_key,
            region,
            gcs_credentials) -> dict:
    """Build an S3 or GCS bucket description from CLI options."""
    if url.startswith('gs://'):
        if gcs_credentials is None:
            raise click.UsageError(f'--gcs-credentials is required for {url}.')
        return apr.gs_bucket(url, gcs_credentials)
    return apr.s3_bucket(url,
                         iam_role_arn=iam_role_arn,
                         access_key=access_key,
                         secret_access_key=secret_access_key,
                         region=region)


@command(async_processing, name='request')
@click.option('--collection',
              required=True,
              help='Data collection type, e.g. sentinel-2-l2a, '
              'sentinel-1-grd, landsat-ot-l2, or byoc-<collection-id>.')
@click.option('--time-from',
              help='Start of the time range, ISO 8601, e.g. '
              '2024-06-01T00:00:00Z.')
@click.option('--time-to', help='End of the time range, ISO 8601.')
@click.option('--max-cloud-coverage',
              type=click.FloatRange(0, 100),
              help='Maximum scene cloud cover, 0 to 100.')
@click.option('--mosaicking-order',
              type=click.Choice(['mostRecent', 'leastRecent', 'leastCC']),
              help='Order in which scenes are mosaicked.')
@click.option('--bbox',
              type=types.CommaSeparatedFloat(),
              help='Bounding box as minx,miny,maxx,maxy in --crs.')
@click.option('--geometry',
              type=types.JSON(),
              help='GeoJSON geometry, Feature or FeatureCollection in --crs. '
              'A JSON string, filename, or - for stdin.')
@click.option('--crs',
              help='CRS URI of --bbox and --geometry, e.g. '
              'http://www.opengis.net/def/crs/EPSG/0/32633. '
              'Defaults to WGS84 longitude/latitude.')
@click.option('--evalscript',
              type=click.File('r'),
              help='Evalscript file, or - for stdin.')
@click.option('--evalscript-url',
              help='s3:// or gs:// URL of a stored evalscript. Uses the '
              'same credential options as --delivery.')
@click.option('--width', type=click.IntRange(1, 10000), help='Width in px.')
@click.option('--height', type=click.IntRange(1, 10000), help='Height in px.')
@click.option('--resx',
              type=float,
              help='Horizontal resolution in --crs units. Use with --resy '
              'instead of --width/--height.')
@click.option('--resy', type=float, help='Vertical resolution in --crs units.')
@click.option('--response',
              'responses',
              multiple=True,
              default=['default:image/tiff'],
              show_default=True,
              metavar='IDENTIFIER:FORMAT',
              help='Output file. IDENTIFIER matches an output id in the '
              'evalscript setup(), or userdata. FORMAT is one of '
              f'{", ".join(FORMATS)}. May be repeated.')
@click.option('--delivery',
              required=True,
              help='s3://bucket/prefix or gs://bucket/prefix. Results are '
              'written to <prefix>/<REQUEST_ID>/ unless the URL contains '
              '<REQUEST_ID> or <OUTPUT> placeholders.')
@click.option('--iam-role-arn',
              help='S3: IAM role for the service to assume. Recommended.')
@click.option('--aws-access-key-id', help='S3: access key ID.')
@click.option('--aws-secret-access-key', help='S3: secret access key.')
@click.option('--aws-region',
              help='S3: bucket region, if it differs from the deployment.')
@click.option('--gcs-credentials',
              type=click.File('rb'),
              help='GCS: service account key JSON file.')
async def request(ctx,
                  collection,
                  time_from,
                  time_to,
                  max_cloud_coverage,
                  mosaicking_order,
                  bbox,
                  geometry,
                  crs,
                  evalscript,
                  evalscript_url,
                  width,
                  height,
                  resx,
                  resy,
                  responses,
                  delivery,
                  iam_role_arn,
                  aws_access_key_id,
                  aws_secret_access_key,
                  aws_region,
                  gcs_credentials,
                  pretty):
    """Generate an async processing request.

    Prints the request JSON. Pass it to `planet async-processing create`.
    No request is sent to the API.

    Give --bbox, --geometry or both. Give --width/--height or --resx/--resy.
    Give --evalscript or --evalscript-url.

    S3 delivery needs --iam-role-arn, or --aws-access-key-id and
    --aws-secret-access-key. GCS delivery needs --gcs-credentials.

    Example:

    \b
    planet async-processing request --collection sentinel-2-l2a \\
        --bbox 12.44,41.87,12.54,41.93 --time-from 2024-06-01T00:00:00Z \\
        --time-to 2024-06-30T23:59:59Z --evalscript ndvi.js \\
        --width 2500 --height 2500 --delivery s3://my-bucket/ndvi \\
        --iam-role-arn arn:aws:iam::123456789012:role/planet
    """
    if (evalscript is None) == (evalscript_url is None):
        raise click.UsageError(
            'Give exactly one of --evalscript and --evalscript-url.')

    if geometry is not None:
        geometry = geojson.geom_from_geojson(geometry)

    # Read once: delivery and the evalscript reference may both use it.
    gcs_creds = None
    if gcs_credentials is not None:
        gcs_creds = base64.b64encode(gcs_credentials.read()).decode()

    def bucket(url):
        return _bucket(url,
                       iam_role_arn,
                       aws_access_key_id,
                       aws_secret_access_key,
                       aws_region,
                       gcs_creds)

    body = apr.build_request(
        input=apr.process_input(data=[
            apr.data_source(collection,
                            time_from=time_from,
                            time_to=time_to,
                            max_cloud_coverage=max_cloud_coverage,
                            mosaicking_order=mosaicking_order)
        ],
                                bbox=bbox,
                                geometry=geometry,
                                crs=crs),
        output=apr.process_output(delivery=bucket(delivery),
                                  width=width,
                                  height=height,
                                  resx=resx,
                                  resy=resy,
                                  responses=_parse_responses(responses)),
        evalscript=evalscript.read() if evalscript else None,
        evalscript_reference=bucket(evalscript_url)
        if evalscript_url else None)
    echo_json(body, pretty)


@command(async_processing, name='create')
@click.argument('request', type=types.JSON())
async def create(ctx, request, pretty):
    """Submit an async processing request.

    REQUEST is the request JSON: a JSON string, a filename, or - for stdin.
    Generate one with `planet async-processing request`.

    Prints the request ID and status. Invalid requests fail here. Errors
    during processing are written to error.json in the delivery bucket.

    Example:

    planet async-processing create request.json
    """
    async with async_processing_client(ctx) as cl:
        result = await cl.create_request(request)
        echo_json(result, pretty)


@command(async_processing, name='get')
@click.argument('request_id')
async def get(ctx, request_id, pretty):
    """Get the status of a running request.

    The API reports only running requests. Once a request finishes,
    successfully or not, this command fails with a not-running message.
    Check the delivery bucket for results or error.json.

    Example:

    planet async-processing get 7d9a1c2e-0000-4000-8000-000000000000
    """
    async with async_processing_client(ctx) as cl:
        try:
            result = await cl.get_request(request_id)
        except exceptions.MissingResource:
            raise click.ClickException(NOT_RUNNING.format(request_id))
        echo_json(result, pretty)


@command(async_processing, name='wait')
@click.argument('request_id')
@click.option('--delay',
              type=click.IntRange(min=0),
              default=10,
              show_default=True,
              help='Time (in seconds) between polls.')
@click.option('--max-attempts',
              type=click.IntRange(min=0),
              default=360,
              show_default=True,
              help='Maximum number of polls. Set to zero for no limit.')
async def wait(ctx, request_id, delay, max_attempts, pretty):
    """Wait until a request is no longer running.

    Polls the request status until the API stops reporting it, then exits
    with status 0. Fails if --max-attempts is reached first.

    Completion does not mean success. Check the delivery bucket for results
    or error.json. An unknown request ID also returns at once, since the
    API reports it the same way as a finished request.

    Example:

    planet async-processing wait 7d9a1c2e-0000-4000-8000-000000000000
    """
    quiet = ctx.obj['QUIET']

    def report(status):
        if not quiet:
            click.echo(f'{request_id}: {status}', err=True)

    async with async_processing_client(ctx) as cl:
        await cl.wait(request_id,
                      delay=delay,
                      max_attempts=max_attempts,
                      callback=report)
    if not quiet:
        click.echo(NOT_RUNNING.format(request_id), err=True)
