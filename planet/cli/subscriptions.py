"""Subscriptions CLI"""

import json

import click

from .cmds import coro, translate_exceptions
from .io import echo_json
from .session import CliSession
from planet.clients.subscriptions import SubscriptionsClient


@click.group()
@click.pass_context
def subscriptions(ctx):
    '''Commands for interacting with the Subscriptions API'''
    pass


# We want our command to be known as "list" on the command line but
# don't want to clobber Python's built-in "list". We'll define the
# command function as "list_subscriptions".
@subscriptions.command(name="list")
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
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
@click.option('--limit',
              type=int,
              default=100,
              help='Maximum number of results to return. Defaults to 100.')
@click.pass_context
@translate_exceptions
@coro
async def list_subscriptions_cmd(ctx, status, limit, pretty):
    """Prints a sequence of JSON-encoded Subscription descriptions."""
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        async for sub in client.list_subscriptions(status=status, limit=limit):
            echo_json(sub, pretty)


def parse_request(ctx, param, value: str) -> dict:
    """Turn request JSON/file into a dict."""
    if value.startswith('{'):
        try:
            obj = json.loads(value)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Request does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
    else:
        try:
            with click.open_file(value) as f:
                obj = json.load(f)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Request does not contain valid json.',
                                     ctx=ctx,
                                     param=param)

    return obj


@subscriptions.command(name='create')
@click.argument('request', callback=parse_request)
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def create_subscription_cmd(ctx, request, pretty):
    """Submits a subscription request and prints the API response."""
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        sub = await client.create_subscription(request)
        echo_json(sub, pretty)


@subscriptions.command(name='cancel')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def cancel_subscription_cmd(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response."""
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        sub = await client.cancel_subscription(subscription_id)
        echo_json(sub, pretty)


@subscriptions.command(name='update')
@click.argument('subscription_id')
@click.argument('request', callback=parse_request)
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def update_subscription_cmd(ctx, subscription_id, request, pretty):
    """Updates a subscription and prints the API response."""
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        sub = await client.update_subscription(subscription_id, request)
        echo_json(sub, pretty)


@subscriptions.command(name='describe')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def describe_subscription_cmd(ctx, subscription_id, pretty):
    """Gets the description of a subscription and prints the API response."""
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        sub = await client.get_subscription(subscription_id)
        echo_json(sub, pretty)


@subscriptions.command(name='results')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
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
@click.option('--limit',
              type=int,
              default=100,
              help='Maximum number of results to return. Defaults to 100.')
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
    async with CliSession() as session:
        client = SubscriptionsClient(session)
        async for result in client.get_results(subscription_id,
                                               status=status,
                                               limit=limit):
            echo_json(result, pretty)
