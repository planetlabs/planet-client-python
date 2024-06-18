"""Subscriptions CLI"""
from contextlib import asynccontextmanager
from typing import List, Optional

import click

from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession
from planet.clients.subscriptions import SubscriptionsClient
from .. import subscription_request
from ..subscription_request import sentinel_hub
from ..specs import get_item_types, validate_item_type, SpecificationException
from .validators import check_geom

ALL_ITEM_TYPES = get_item_types()
valid_item_string = "Valid entries for ITEM_TYPES: " + "|".join(ALL_ITEM_TYPES)


def check_item_types(ctx, param, item_types) -> Optional[List[dict]]:
    """Validates each item types provided by comparing them to all supported
    item types."""
    try:
        for item_type in item_types:
            validate_item_type(item_type)
        return item_types
    except SpecificationException as e:
        raise click.BadParameter(str(e))


def check_item_type(ctx, param, item_type) -> Optional[List[dict]]:
    """Validates the item type provided by comparing it to all supported
    item types."""
    try:
        validate_item_type(item_type)
    except SpecificationException as e:
        raise click.BadParameter(str(e))

    return item_type


@asynccontextmanager
async def subscriptions_client(ctx):
    async with CliSession() as sess:
        cl = SubscriptionsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Subscriptions API URL.')
def subscriptions(ctx, base_url):
    """Commands for interacting with the Subscriptions API"""
    ctx.obj['BASE_URL'] = base_url


# We want our command to be known as "list" on the command line but
# don't want to clobber Python's built-in "list". We'll define the
# command function as "list_subscriptions".
@subscriptions.command(name="list")  # type: ignore
@pretty
@click.option(
    '--status',
    type=click.Choice([
        "running",
        "cancelled",
        "preparing",
        "pending",
        "completed",
        "suspended",
        "failed"
    ]),
    multiple=True,
    default=None,
    help="Select subscriptions in one or more states. Default is all.")
@limit
@click.pass_context
@translate_exceptions
@coro
async def list_subscriptions_cmd(ctx, status, limit, pretty):
    """Prints a sequence of JSON-encoded Subscription descriptions."""
    async with subscriptions_client(ctx) as client:
        async for sub in client.list_subscriptions(status=status, limit=limit):
            echo_json(sub, pretty)


@subscriptions.command(name="create")  # type: ignore
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
@click.pass_context
@translate_exceptions
@coro
async def create_subscription_cmd(ctx, request, pretty, **kwargs):
    """Create a subscription.

    Submits a subscription request for creation and prints the created
    subscription description, optionally pretty-printed.

    REQUEST is the full description of the subscription to be created. It must
    be JSON and can be specified a json string, filename, or '-' for stdin.

    Other flag options are hosting and collection_id. The hosting flag
    specifies the hosting type, and the collection_id flag specifies the
    collection ID for Sentinel Hub. If the collection_id is omitted, a new
    collection will be created.
    """

    hosting = kwargs.get("hosting", None)
    collection_id = kwargs.get("collection_id", None)

    if hosting == "sentinel_hub":
        hosting_info = sentinel_hub(collection_id)
        request["hosting"] = hosting_info

    async with subscriptions_client(ctx) as client:
        sub = await client.create_subscription(request)
        echo_json(sub, pretty)


@subscriptions.command(name='cancel')  # type: ignore
@click.argument('subscription_id')
@pretty
@click.pass_context
@translate_exceptions
@coro
async def cancel_subscription_cmd(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        _ = await client.cancel_subscription(subscription_id)


@subscriptions.command(name='update')  # type: ignore
@click.argument('subscription_id')
@click.argument('request', type=types.JSON())
@pretty
@click.pass_context
@translate_exceptions
@coro
async def update_subscription_cmd(ctx, subscription_id, request, pretty):
    """Update a subscription via PUT.

    Updates a subscription and prints the updated subscription description,
    optionally pretty-printed.

    REQUEST is the full description of the updated subscription. It must be
    JSON and can be specified a json string, filename, or '-' for stdin.
    """
    async with subscriptions_client(ctx) as client:
        sub = await client.update_subscription(subscription_id, request)
        echo_json(sub, pretty)


@subscriptions.command(name='patch')  # type: ignore
@click.argument('subscription_id')
@click.argument('request', type=types.JSON())
@pretty
@click.pass_context
@translate_exceptions
@coro
async def patch_subscription_cmd(ctx, subscription_id, request, pretty):
    """Update a subscription via PATCH.

    Updates a subscription and prints the updated subscription description,
    optionally pretty-printed.

    REQUEST only requires the attributes to be changed. It must be
    JSON and can be specified a json string, filename, or '-' for stdin.
    """
    async with subscriptions_client(ctx) as client:
        sub = await client.patch_subscription(subscription_id, request)
        echo_json(sub, pretty)


@subscriptions.command(name='get')  # type: ignore
@click.argument('subscription_id')
@pretty
@click.pass_context
@translate_exceptions
@coro
async def get_subscription_cmd(ctx, subscription_id, pretty):
    """Get the description of a subscription."""
    async with subscriptions_client(ctx) as client:
        sub = await client.get_subscription(subscription_id)
        echo_json(sub, pretty)


@subscriptions.command(name='results')  # type: ignore
@click.argument('subscription_id')
@pretty
@click.option(
    '--status',
    type=click.Choice(["created", "queued", "processing", "failed",
                       "success"]),
    multiple=True,
    default=None,
    callback=(lambda ctx, param, value: set(value)),
    help="Select subscription results in one or more states. Default: all.")
@click.option('--csv',
              'csv_flag',
              is_flag=True,
              default=False,
              help="Get subscription results as comma-separated fields.")
@limit
# TODO: the following 3 options.
# –created: timestamp instant or range.
# –updated: timestamp instant or range.
# –completed: timestamp instant or range.
@click.pass_context
@translate_exceptions
@coro
async def list_subscription_results_cmd(ctx,
                                        subscription_id,
                                        pretty,
                                        status,
                                        csv_flag,
                                        limit):
    """Print the results of a subscription to stdout.

    The output of this command is a sequence of JSON objects (the
    default) or a sequence of comma-separated fields (when the --csv
    option is used), one result per line.

    Examples:

    \b
        planet subscriptions results SUBSCRIPTION_ID --status=success --limit 10

    Where SUBSCRIPTION_ID is the unique identifier for a subscription,
    this prints the last 10 successfully delivered results for that
    subscription as JSON objects.

    \b
        planet subscriptions results SUBSCRIPTION_ID --limit 0 --csv > results.csv

    Prints all results for a subscription and saves them to a CSV file.
    """
    async with subscriptions_client(ctx) as client:
        if csv_flag:
            async for result in client.get_results_csv(subscription_id,
                                                       status=status,
                                                       limit=limit):
                click.echo(result)
        else:
            async for result in client.get_results(subscription_id,
                                                   status=status,
                                                   limit=limit):
                echo_json(result, pretty)


@subscriptions.command()  # type: ignore
@translate_exceptions
@click.option('--name',
              required=True,
              type=str,
              help='Subscription name. Does not need to be unique.')
@click.option('--source',
              required=True,
              type=types.JSON(),
              help='Source JSON. Can be a string, filename, or - for stdin.')
@click.option(
    '--delivery',
    type=types.JSON(),
    help=("Delivery configuration, including credentials for a cloud "
          "storage provider, to enable cloud delivery of data. Can be a "
          "JSON string, a filename, or '-' for stdin. "))
@click.option(
    '--notifications',
    type=types.JSON(),
    help='Notifications JSON. Can be a string, filename, or - for stdin.')
@click.option(
    '--tools',
    type=types.JSON(),
    help='Toolchain JSON. Can be a string, filename, or - for stdin.')
@click.option(
    '--hosting',
    default=None,
    type=click.Choice([
        "sentinel_hub",
    ]),
    help='Hosting configuration. Can be JSON, "sentinel_hub", or omitted.')
@click.option(
    '--clip-to-source',
    is_flag=True,
    default=False,
    help="Clip to the source geometry without specifying a clip tool.")
@click.option("--collection-id",
              default=None,
              help='Collection ID for Sentinel Hub hosting. '
              'If omitted, a new collection will be created.')
@pretty
def request(name,
            source,
            delivery,
            notifications,
            tools,
            hosting,
            collection_id,
            clip_to_source,
            pretty):
    """Generate a subscriptions request.

    Note: the next version of the Subscription API will remove the clip
    tool option and always clip to the source geometry. Thus the
    --clip-to-source option is a preview of the next API version's
    default behavior.
    """

    res = subscription_request.build_request(name,
                                             source,
                                             delivery,
                                             notifications=notifications,
                                             tools=tools,
                                             hosting=hosting,
                                             collection_id=collection_id,
                                             clip_to_source=clip_to_source)
    echo_json(res, pretty)


@subscriptions.command(epilog=valid_item_string)  # type: ignore
@translate_exceptions
@click.option('--item-types',
              required=True,
              help='Item type for requested item ids.',
              type=types.CommaSeparatedString(),
              callback=check_item_types)
@click.option('--asset-types',
              required=True,
              type=types.CommaSeparatedString(),
              help='One or more comma-separated asset types.')
@click.option(
    '--geometry',
    required=True,
    type=types.Geometry(),
    callback=check_geom,
    help="""Geometry of the area of interest of the subscription that will be
    used to determine matches. Can be a string, filename, or - for stdin.""")
@click.option('--start-time',
              required=True,
              type=types.DateTime(),
              help='Date and time to begin subscription.')
@click.option('--end-time',
              type=types.DateTime(),
              help='Date and time to end subscription.')
@click.option('--rrule',
              type=str,
              help='iCalendar recurrance rule to specify recurrances.')
@click.option(
    '--filter',
    type=types.JSON(),
    help='Search filter.  Can be a string, filename, or - for stdin.')
@click.option(
    '--publishing-stage',
    'publishing_stages',
    type=click.Choice(["preview", "standard", "finalized"]),
    multiple=True,
    help=("Subscribe to results at a particular publishing stage. Multiple "
          "instances of this option are allowed."))
@click.option('--time-range-type',
              type=click.Choice(["acquired", "published"]),
              help="Subscribe by acquisition time or time of publication.")
@pretty
def request_catalog(item_types,
                    asset_types,
                    geometry,
                    start_time,
                    end_time,
                    rrule,
                    filter,
                    publishing_stages,
                    time_range_type,
                    pretty):
    """Generate a subscriptions request catalog source description."""

    res = subscription_request.catalog_source(
        item_types,
        asset_types,
        geometry,
        start_time,
        end_time=end_time,
        rrule=rrule,
        filter=filter,
        publishing_stages=publishing_stages,
        time_range_type=time_range_type)
    echo_json(res, pretty)


@subscriptions.command()  # type: ignore
@translate_exceptions
@click.option(
    '--var-type',
    required=True,
    help='A Planetary Variable type. See documentation for all available types.'
)
@click.option(
    '--var-id',
    required=True,
    help='A Planetary Variable ID. See documenation for all available IDs.')
@click.option(
    '--geometry',
    required=True,
    type=types.Geometry(),
    callback=check_geom,
    help="""Geometry of the area of interest of the subscription that will be
    used to determine matches. Can be a string, filename, or - for stdin.""")
@click.option('--start-time',
              required=True,
              type=types.DateTime(),
              help='Date and time to begin subscription.')
@click.option('--end-time',
              type=types.DateTime(),
              help='Date and time to end subscription.')
@pretty
def request_pv(var_type, var_id, geometry, start_time, end_time, pretty):
    """Generate a Planetary Variable subscription source.

    Planetary Variables come in 4 types and are further subdivided
    within these types. See [Subscribing to Planetary Variables](https://developers.planet.com/docs/subscriptions/pvs-subs/#planetary-variables-types-and-ids)
    or the [OpenAPI spec](https://api.planet.com/subscriptions/v1/spec) for
    more details.
    """
    res = subscription_request.planetary_variable_source(
        var_type,
        var_id,
        geometry,
        start_time,
        end_time=end_time,
    )
    echo_json(res, pretty)
