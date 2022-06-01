"""Subscriptions CLI"""

from contextlib import asynccontextmanager
import itertools
import json
from typing import AsyncIterator, Dict, Set
import uuid

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


class PlaceholderSubscriptionsClient:
    """A placeholder client.

    This class and its methods are derived from tests of a skeleton
    Subscriptions CLI.

    """

    async def list_subscriptions(self,
                                 status: Set[str] = None,
                                 limit: int = 100) -> AsyncIterator[dict]:
        """Get Subscriptions.

        Parameters:
            status
            limit

        Yields:
            dict

        """
        if status:
            select_subs = (dict(**sub, id=sub_id) for sub_id,
                           sub in _fake_subs.items()
                           if sub['status'] in status)
        else:
            select_subs = (
                dict(**sub, id=sub_id) for sub_id, sub in _fake_subs.items())

        filtered_subs = itertools.islice(select_subs, limit)

        for sub in filtered_subs:
            yield sub

    async def create_subscription(self, request: dict) -> dict:
        """Create a Subscription.

        Parameters:
            request

        Returns:
            dict

        Raises:
            PlanetError

        """
        missing_keys = {'name', 'delivery', 'source'} - request.keys()
        if missing_keys:
            raise PlanetError(
                f"Request lacks required members: {missing_keys!r}")

        id = str(uuid.uuid4())
        _fake_subs[id] = request
        sub = _fake_subs[id].copy()
        sub.update(id=id)
        return sub

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            sub = _fake_subs.pop(subscription_id)
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def update_subscription(self, subscription_id: str,
                                  request: dict) -> dict:
        """Update (edit) a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            _fake_subs[subscription_id].update(**request)
            sub = _fake_subs[subscription_id].copy()
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def get_subscription(self, subscription_id: str) -> dict:
        """Get a description of a Subscription.

        Parameters:
            subscription_id

        Returns:
            dict

        Raises:
            PlanetError

        """
        try:
            sub = _fake_subs[subscription_id].copy()
        except KeyError:
            raise PlanetError(f"No such subscription: {subscription_id!r}")

        sub.update(id=subscription_id)
        return sub

    async def list_subscription_results(
            self,
            subscription_id: str,
            status: Set[str] = None,
            limit: int = 100) -> AsyncIterator[dict]:
        """Get Results of a Subscription.

        Parameters:
            subscription_id
            status
            limit

        Yields:
            dict

        Raises:
            PlanetError

        """
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
    """Create an authenticated client.

    Note that the session is not currently used with the placeholder
    client.

    """
    auth = ctx.obj['AUTH']
    async with Session(auth=auth):
        yield PlaceholderSubscriptionsClient()


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
async def list_subscriptions_cmd(ctx, status, limit, pretty):
    """Prints a sequence of JSON-encoded Subscription descriptions."""
    async with subscriptions_client(ctx) as client:
        filtered_subs = client.list_subscriptions(status=status, limit=limit)
        async for sub in filtered_subs:
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
    async with subscriptions_client(ctx) as client:
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
    async with subscriptions_client(ctx) as client:
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
    """Cancels a subscription and prints the API response."""
    async with subscriptions_client(ctx) as client:
        sub = await client.update_subscription(subscription_id, request)
        echo_json(sub, pretty)


@subscriptions.command(name='describe')
@click.argument('subscription_id')
@click.option('--pretty', is_flag=True, help='Pretty-print output.')
@click.pass_context
@translate_exceptions
@coro
async def describe_subscription_cmd(ctx, subscription_id, pretty):
    """Cancels a subscription and prints the API response.

    This implementation is only a placeholder. To begin, instead
    of mocking calls to the Subscriptions API, we'll use a
    collection of fake subscriptions (the all_subs object).
    After we refactor we will change to mocking the API.

    """
    async with subscriptions_client(ctx) as client:
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
    async with subscriptions_client(ctx) as client:
        filtered_results = client.list_subscription_results(subscription_id,
                                                            status=status,
                                                            limit=limit)
        async for result in filtered_results:
            echo_json(result, pretty)
