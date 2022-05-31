"""Subscriptions CLI"""

from contextlib import asynccontextmanager
import itertools
import json
from typing import AsyncIterator, Dict, Set

import click

import planet
from planet import Session
from planet.cli.cmds import coro, translate_exceptions
from planet.cli.io import echo_json
from planet.exceptions import PlanetError

# Collections of fake subscriptions and results for testing. Tests will
# monkeypatch these attributes.
_fake_subs: Dict[str, dict] = {}
_fake_sub_results: Dict[str, list] = {}


# The following 5 functions are for use in CLI commands until there
# is subscriptions Python client to call on.
def _count_fake_subs():
    return len(_fake_subs)


def _cancel_fake_sub(sub_id):
    return _fake_subs.pop(sub_id)


def _update_fake_sub(sub_id, **kwds):
    _fake_subs[sub_id].update(**kwds)
    return _get_fake_sub(sub_id)


def _get_fake_sub(sub_id):
    sub = _fake_subs[sub_id].copy()
    sub.update(id=sub_id)
    return sub


class PlaceholderSubscriptionsClient:

    def __init__(self, session):
        # Note: placeholder doesn't use the session (yet).
        self.session = session

    async def list_results(self,
                           subscription_id: str,
                           status: Set[str] = None,
                           limit: int = 100) -> AsyncIterator[dict]:
        try:
            if status:
                select_results = (
                    result for result in _fake_sub_results[subscription_id]
                    if result['status'] in status)
            else:
                select_results = (
                    result for result in _fake_sub_results[subscription_id])

            filtered_results = itertools.islice(select_results, limit)
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        for result in filtered_results:
            yield result


@asynccontextmanager
async def subscriptions_client(ctx):
    auth = ctx.obj['AUTH']
    async with Session(auth=auth) as sess:
        yield PlaceholderSubscriptionsClient(sess)


@click.group()
@click.pass_context
def subscriptions(ctx):
    ctx.obj['AUTH'] = planet.Auth.from_file()


# We want our command to be known as "list" on the command line but
# don't want to clobber Python's built-in "list". We'll define the
# command function as "list_subscriptions".
@subscriptions.command(name="list")
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.option(
    '--status',
    type=click.Choice(["created", "queued", "processing", "failed",
                       "success"]),
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
async def list_subscriptions(ctx, status, limit, pretty):
    """Prints a sequence of JSON-encoded Subscription descriptions.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs fixture).
    After we refactor we will change to mocking the API.

    """
    # Filter by status, like the Subscriptions API does.
    if status:
        select_subs = (sub for sub in _fake_subs if sub['status'] in status)
    else:
        select_subs = _fake_subs

    filtered_subs = itertools.islice(select_subs, limit)
    # End of placeholder implementation. In the future we will get
    # the filtered subscriptions from a method of the to-be-written
    # planet.clients.subscriptions.

    # Print output to terminal, respecting the provided limit.
    for sub in filtered_subs:
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
async def create_subscription(ctx, request, pretty):
    """Submits a subscription request and prints the API response.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs object).
    After we refactor we will change to mocking the API.

    """
    # Begin fake subscriptions service. Note that the Subscriptions
    # API will report missing keys differently, but the Python API
    # *will* raise PlanetError like this.
    missing_keys = {'name', 'delivery', 'source'} - request.keys()
    if missing_keys:
        raise PlanetError(f"Request lacks required members: {missing_keys!r}")

    # Update the request with an id.
    sub = dict(**request, id='42')
    _fake_subs.append(sub)

    # End fake subscriptions service. After we refactor we will get
    # the "sub" from a method in planet.clients.subscriptions (which
    # doesn't exist yet).

    echo_json(sub, pretty)


@subscriptions.command(name='cancel')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def cancel_subscription(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs object).
    After we refactor we will change to mocking the API.

    """
    # Begin fake subscriptions service. Note that the Subscriptions
    # API will report missing keys differently, but the Python API
    # *will* raise PlanetError like this.
    try:
        sub = _cancel_fake_sub(subscription_id)
    except KeyError:
        raise PlanetError(f"No such subscription: {subscription_id!r}")

    # End fake subscriptions service. After we refactor we will get
    # the "sub" from a method in planet.clients.subscriptions (which
    # doesn't exist yet).

    echo_json(sub, pretty)


@subscriptions.command(name='update')
@click.argument('subscription_id')
@click.argument('request', callback=parse_request)
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def update_subscription(ctx, subscription_id, request, pretty):
    """Cancels a subscription and prints the API response.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs object).
    After we refactor we will change to mocking the API.

    """
    # Begin fake subscriptions service. Note that the Subscriptions
    # API will report missing keys differently, but the Python API
    # *will* raise PlanetError like this.
    try:
        sub = _update_fake_sub(subscription_id, **request)
    except KeyError:
        raise PlanetError(f"No such subscription: {subscription_id!r}")

    # End fake subscriptions service. After we refactor we will get
    # the "sub" from a method in planet.clients.subscriptions (which
    # doesn't exist yet).

    echo_json(sub, pretty)


@subscriptions.command(name='describe')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def describe_subscription(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs object).
    After we refactor we will change to mocking the API.

    """
    # Begin fake subscriptions service. Note that the Subscriptions
    # API will report missing keys differently, but the Python API
    # *will* raise PlanetError like this.
    try:
        sub = _get_fake_sub(subscription_id)
    except KeyError:
        raise PlanetError(f"No such subscription: {subscription_id!r}")

    # End fake subscriptions service. After we refactor we will get
    # the "sub" from a method in planet.clients.subscriptions (which
    # doesn't exist yet).

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
async def list_subscription_results(ctx,
                                    subscription_id,
                                    pretty,
                                    status,
                                    limit):
    """Gets results of a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        filtered_results = client.list_results(subscription_id,
                                               status=status,
                                               limit=limit)
        async for result in filtered_results:
            echo_json(result, pretty)
