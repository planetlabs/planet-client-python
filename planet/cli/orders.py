# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Orders API CLI"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path

import click

import planet
from planet import OrdersClient  # allow mocking
from . import types
from .cmds import coro, translate_exceptions
from ..order_request import sentinel_hub
from .io import echo_json
from .options import limit, pretty
from .session import CliSession

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def orders_client(ctx):
    base_url = ctx.obj['BASE_URL']
    async with CliSession() as sess:
        cl = OrdersClient(sess, base_url=base_url)
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def orders(ctx, base_url):
    """Commands for interacting with the Orders API"""
    ctx.obj['BASE_URL'] = base_url


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.option('--state',
              help='Filter by state.',
              type=click.Choice(planet.clients.orders.ORDER_STATE_SEQUENCE,
                                case_sensitive=False))
@click.option(
    '--source-type',
    default="all",
    help="""Filter by source type. See documentation for all available types.
    Default is all.""")
@click.option('--name', help="filter by name")
@click.option(
    '--name-contains',
    help="only return orders with a name that contains the provided string.")
@click.option(
    '--created-on',
    help="Filter by creation time or interval. See documentation for examples."
)
@click.option(
    '--last-modified',
    help="Filter by creation time or interval. See documentation for examples."
)
@click.option(
    '--hosting',
    type=click.BOOL,
    help="Filter by presence of hosting block (e.g. SentinelHub hosting).")
@click.option(
    '--sort-by',
    help="""fields to sort orders by. Multiple fields can be specified,
    separated by commas. The sort direction can be specified by appending
    ' ASC' or ' DESC' to the field name. The default sort direction is
    ascending. When multiple fields are specified, the sort order is applied
    in the order the fields are listed.

    Supported fields: [name, created_on, state, last_modified].

    Example: 'name ASC,created_on DESC'""")
@limit
@pretty
async def list(ctx,
               state,
               source_type,
               name,
               name_contains,
               created_on,
               last_modified,
               hosting,
               sort_by,
               limit,
               pretty):
    """List orders

    This command prints a sequence of the returned order descriptions,
    optionally pretty-printed.

    By default, order descriptions are sorted by creation date with the last created order
    returned first.
    """
    async with orders_client(ctx) as cl:
        async for o in cl.list_orders(state=state,
                                      source_type=source_type,
                                      name=name,
                                      name__contains=name_contains,
                                      created_on=created_on,
                                      last_modified=last_modified,
                                      hosting=hosting,
                                      sort_by=sort_by,
                                      limit=limit):
            echo_json(o, pretty)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@pretty
async def get(ctx, order_id, pretty):
    """Get order

    This command outputs the order description, optionally pretty-printed.
    """
    async with orders_client(ctx) as cl:
        order = await cl.get_order(str(order_id))

    echo_json(order, pretty)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
async def cancel(ctx, order_id):
    """Cancel order by order ID.

    This command cancels a queued order and outputs the cancelled order
    details.
    """
    async with orders_client(ctx) as cl:
        json_resp = await cl.cancel_order(str(order_id))

    click.echo(json_resp)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@click.option('--delay',
              type=int,
              default=5,
              help='Time (in seconds) between polls.')
@click.option('--max-attempts',
              type=int,
              default=200,
              show_default=True,
              help='Maximum number of polls. Set to zero for no limit.')
@click.option('--state',
              help='State prior to a final state that will end polling.',
              type=click.Choice(planet.clients.orders.ORDER_STATE_SEQUENCE,
                                case_sensitive=False))
async def wait(ctx, order_id, delay, max_attempts, state):
    """Wait until order reaches desired state.

    Reports the state of the order on the last poll.

    This function polls the Orders API to determine the order state, with
    the specified delay between each polling attempt, until the
    order reaches a final state or earlier state, if specified.
    If the maximum number of attempts is reached before polling is
    complete, an exception is raised. Setting --max-attempts to zero will
    result in no limit on the number of attempts.

    Setting --delay to zero results in no delay between polling attempts.
    This will likely result in throttling by the Orders API, which has
    a rate limit of 10 requests per second. If many orders are being
    polled asynchronously, consider increasing the delay to avoid
    throttling.

    By default, polling completes when the order reaches a final state.
    If --state is specified, polling will complete when the specified earlier
    state is reached or passed.
    """
    quiet = ctx.obj['QUIET']
    async with orders_client(ctx) as cl:
        with planet.reporting.StateBar(order_id=order_id,
                                       disable=quiet) as bar:
            state = await cl.wait(str(order_id),
                                  state=state,
                                  delay=delay,
                                  max_attempts=max_attempts,
                                  callback=bar.update_state)
    click.echo(state)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('order_id', type=click.UUID)
@click.option('--checksum',
              default=None,
              type=click.Choice(['MD5', 'SHA256'], case_sensitive=False),
              help=('Verify that checksums match.'))
@click.option('--directory',
              default='.',
              help=('Base directory for file download.'),
              type=click.Path(exists=True,
                              resolve_path=True,
                              writable=True,
                              file_okay=False))
@click.option('--overwrite',
              is_flag=True,
              default=False,
              help=('Overwrite files if they already exist.'))
async def download(ctx, order_id, overwrite, directory, checksum):
    """Download order by order ID.

    If --checksum is provided, the associated checksums given in the manifest
    are compared against the downloaded files to verify that they match.

    If --checksum is provided, files are already downloaded, and --overwrite is
    not specified, this will simply validate the checksums of the files against
    the manifest.
    """
    quiet = ctx.obj['QUIET']
    async with orders_client(ctx) as cl:
        await cl.download_order(
            str(order_id),
            directory=Path(directory),
            overwrite=overwrite,
            progress_bar=not quiet,
        )
        if checksum:
            cl.validate_checksum(Path(directory, str(order_id)), checksum)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("request", type=types.JSON())
@click.option(
    "--hosting",
    type=click.Choice([
        "sentinel_hub",
    ]),
    default=None,
    help='Hosting type. Currently, only "sentinel_hub" is supported.',
)
@click.option("--collection-id",
              default=None,
              help='Collection ID for Sentinel Hub hosting. '
              'If omitted, a new collection will be created.')
@pretty
async def create(ctx, request, pretty, **kwargs):
    """Create an order.

    This command outputs the created order description, optionally
    pretty-printed.

    REQUEST is the full description of the order to be created. It must be JSON
    and can be specified a json string, filename, or '-' for stdin.

    Other flag options are hosting and collection_id. The hosting flag
    specifies the hosting type, and the collection_id flag specifies the
    collection ID for Sentinel Hub. If the collection_id is omitted, a new
    collection will be created.
    """

    hosting = kwargs.get('hosting')
    collection_id = kwargs.get('collection_id')

    if hosting == "sentinel_hub":
        request["hosting"] = sentinel_hub(collection_id)

    async with orders_client(ctx) as cl:
        order = await cl.create_order(request)

    echo_json(order, pretty)


@orders.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument('ids', metavar='IDS', type=types.CommaSeparatedString())
@click.option('--item-type',
              required=True,
              help='Item type for requested item ids.',
              type=click.Choice(planet.specs.get_item_types(),
                                case_sensitive=False))
@click.option('--bundle',
              required=True,
              help='Asset type for the item.',
              type=click.Choice(planet.specs.get_product_bundles(),
                                case_sensitive=False))
@click.option('--name',
              required=True,
              help='Order name. Does not need to be unique.',
              type=click.STRING)
@click.option('--clip',
              type=types.JSON(),
              help="""Clip feature Polygon or Multipolygon GeoJSON. Can be a
              json string, filename, or '-' for stdin.""")
@click.option(
    '--tools',
    type=types.JSON(),
    help="""Toolchain JSON. Can be a json string, filename, or '-' for
    stdin.""")
@click.option('--email',
              default=False,
              is_flag=True,
              help='Send email notification when order is complete.')
@click.option('--archive-type',
              type=click.Choice(['zip']),
              help="Optionally zip archive each item bundle.")
@click.option('--archive-filename',
              default='{{name}}-{{order_id}}.zip',
              show_default=True,
              help="Templated filename for archived bundles or orders.")
@click.option('--single-archive',
              is_flag=True,
              default=False,
              show_default=True,
              help="Optionally zip archive all item bundles together.")
@click.option(
    '--delivery',
    '--cloudconfig',
    type=types.JSON(),
    help=("Delivery configuration, which may include credentials for a cloud "
          "storage provider, to enable cloud delivery of data, and/or "
          "parameters for bundling deliveries as zip archives. Can be a JSON "
          "string, a filename, or '-' for stdin. The --cloudconfig option is "
          "an alias for this use case."))
@click.option(
    '--stac/--no-stac',
    default=True,
    is_flag=True,
    help="""Include or exclude metadata in SpatioTemporal Asset Catalog (STAC)
    format. Not specifying either defaults to including it (--stac), except
    for orders with google_earth_engine delivery""")
@click.option('--hosting',
              type=click.Choice(['sentinel_hub']),
              help='Hosting for data delivery. '
              'Currently, only "sentinel_hub" is supported.')
@click.option('--collection_id',
              help='Collection ID for Sentinel Hub hosting. '
              'If omitted, a new collection will be created.')
@pretty
async def request(ctx,
                  item_type,
                  bundle,
                  name,
                  ids,
                  clip,
                  tools,
                  email,
                  archive_type,
                  archive_filename,
                  single_archive,
                  delivery,
                  stac,
                  hosting,
                  collection_id,
                  pretty):
    """Generate an order request.

    This command provides support for building an order description used
    in creating an order. It outputs the order request, optionally
    pretty-printed.

    IDs is one or more comma-separated item IDs.
    """
    try:
        product = planet.order_request.product(ids, bundle, item_type)
    except planet.specs.SpecificationException as e:
        raise click.BadParameter(e)

    if email:
        notifications = planet.order_request.notifications(email=email)
    else:
        notifications = None

    if clip and tools:
        raise click.BadParameter("Specify only one of '--clip' or '--tools'")
    elif clip:
        try:
            tools = [planet.order_request.clip_tool(clip)]
        except planet.exceptions.ClientError as e:
            raise click.BadParameter(e)

    delivery = planet.order_request.delivery(archive_type=archive_type,
                                             archive_filename=archive_filename,
                                             single_archive=single_archive,
                                             cloud_config=delivery)

    if stac and "google_earth_engine" not in delivery:
        stac_json = {'stac': {}}
    else:
        stac_json = {}

    request = planet.order_request.build_request(name,
                                                 products=[product],
                                                 delivery=delivery,
                                                 notifications=notifications,
                                                 tools=tools,
                                                 stac=stac_json,
                                                 hosting=hosting,
                                                 collection_id=collection_id)

    echo_json(request, pretty)
