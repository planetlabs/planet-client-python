"""Subscriptions CLI"""
from contextlib import asynccontextmanager

import click

from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import limit, pretty
from .session import CliSession
from planet.clients.subscriptions import SubscriptionsClient


@asynccontextmanager
async def subscriptions_client(ctx):
    async with CliSession() as sess:
        cl = SubscriptionsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Subscriptions API URL.')
def subscriptions(ctx, base_url):
    '''Commands for interacting with the Subscriptions API'''
    ctx.obj['BASE_URL'] = base_url


# We want our command to be known as "list" on the command line but
# don't want to clobber Python's built-in "list". We'll define the
# command function as "list_subscriptions".
@subscriptions.command(name="list")
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


@subscriptions.command(name='create')
@click.argument('request', type=types.JSON())
@pretty
@click.pass_context
@translate_exceptions
@coro
async def create_subscription_cmd(ctx, request, pretty):
    """Create a subscription.

    Submits a subscription request for creation and prints the created
    subscription description, optionally pretty-printed.

    REQUEST is the full description of the subscription to be created. It must
    be JSON and can be specified a json string, filename, or '-' for stdin.
    """
    async with subscriptions_client(ctx) as client:
        sub = await client.create_subscription(request)
        echo_json(sub, pretty)


@subscriptions.command(name='cancel')
@click.argument('subscription_id')
@pretty
@click.pass_context
@translate_exceptions
@coro
async def cancel_subscription_cmd(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        _ = await client.cancel_subscription(subscription_id)


@subscriptions.command(name='update')
@click.argument('subscription_id')
@click.argument('request', type=types.JSON())
@pretty
@click.pass_context
@translate_exceptions
@coro
async def update_subscription_cmd(ctx, subscription_id, request, pretty):
    """Update a subscription.

    Updates a subscription and prints the updated subscription description,
    optionally pretty-printed.

    REQUEST is the full description of the updated subscription. It must be
    JSON and can be specified a json string, filename, or '-' for stdin.
    """
    async with subscriptions_client(ctx) as client:
        sub = await client.update_subscription(subscription_id, request)
        echo_json(sub, pretty)


@subscriptions.command(name='describe')
@click.argument('subscription_id')
@pretty
@click.pass_context
@translate_exceptions
@coro
async def describe_subscription_cmd(ctx, subscription_id, pretty):
    """Gets the description of a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        sub = await client.get_subscription(subscription_id)
        echo_json(sub, pretty)


@subscriptions.command(name='results')
@click.argument('subscription_id')
@pretty
@click.option(
    '--status',
    type=click.Choice(["created", "queued", "processing", "failed",
                       "success"]),
    multiple=True,
    default=None,
    callback=lambda ctx,
    param,
    value: set(value),
    help="Select subscription results in one or more states. Default: all.")
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
                                        limit):
    """Gets results of a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        async for result in client.get_results(subscription_id,
                                               status=status,
                                               limit=limit):
            echo_json(result, pretty)
