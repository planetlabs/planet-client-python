"""Tests of the Subscriptions CLI (aka planet-subscriptions)

There are 6 subscriptions commands:

planet subscriptions list
planet subscriptions describe
planet subscriptions results
planet subscriptions create
planet subscriptions update
planet subscriptions cancel

"""

import itertools
import json

import click
from click.testing import CliRunner

import pytest

import planet
from planet.cli import cli
from planet.cli.cmds import coro, translate_exceptions
from planet.cli.io import echo_json
from planet.exceptions import PlanetError


@pytest.fixture
def all_subs():
    """A collection of fake subscriptions for testing.

    We're not testing the actual API workflow. All subscription states
    are equal as far as the initial tests are concerned. We have 101
    fake subscriptions so that we can test the command's default limit
    of 100.

    """
    return [{'id': str(i), 'status': 'created'} for i in range(101)]


# CliRunner doesn't agree with empty options, so a list of option
# combinations which omit the empty options is best. For example,
# parametrizing 'limit' as '' and then executing
#
# CliRunner().invoke(cli.main, args=['subscriptions', 'list', limit]
#
# does not work.
@pytest.mark.parametrize('options,expected_count',
                         [(['--status=created'], 100), ([], 100),
                          (['--limit=1', '--status=created'], 1),
                          (['--limit=2', '--pretty', '--status=created'], 2),
                          (['--limit=1', '--status=queued'], 0)])
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_list_options(options, expected_count, all_subs):
    """Prints the expected sequence of subscriptions."""

    # As an exercise in test-driven development, let's develop the CLI
    # right here in the body of the test. Once we have basic tests of
    # the input/output/options working, we can refactor and move the
    # command to planet/cli/subscriptions.py.
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
        type=click.Choice(
            ["created", "queued", "processing", "failed", "success"]),
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
            select_subs = (sub for sub in all_subs if sub['status'] in status)
        else:
            select_subs = all_subs

        filtered_subs = itertools.islice(select_subs, limit)
        # End of placeholder implementation. In the future we will get
        # the filtered subscriptions from a method of the to-be-written
        # planet.clients.subscriptions.

        # Print output to terminal, respecting the provided limit.
        for sub in filtered_subs:
            echo_json(sub, pretty)

    cli.main.add_command(subscriptions)
    # End of the command code.

    # While developing it is handy to have click's command invoker
    # *not* catch exceptions, so we can use the pytest --pdb option.
    result = CliRunner().invoke(cli.main,
                                args=['subscriptions', 'list'] + options,
                                catch_exceptions=False)
    assert result.exit_code == 0  # success.

    # For a start, counting the number of "id" strings in the output
    # tells us how many subscription JSONs were printed, pretty or not.
    assert result.output.count('"id"') == expected_count


def test_subscriptions_create_failure():
    """An invalid subscription request fails to create a new subscription.

    As above, we develop the command here in the body of the test.

    """
    # Begin command's code skeleton.
    @click.group()
    @click.pass_context
    def subscriptions(ctx):
        ctx.obj['AUTH'] = planet.Auth.from_file()

    def parse_request(ctx, param, value: str) -> dict:
        """Turn request JSON/file into a dict."""
        if value.startswith('{'):
            try:
                obj = json.loads(value)
            except json.decoder.JSONDecodeError:
                raise click.BadParameter(
                    'Request does not contain valid json.',
                    ctx=ctx,
                    param=param)
            if not obj:
                raise click.BadParameter('Request is empty.',
                                         ctx=ctx,
                                         param=param)
        else:
            try:
                with click.open_file(value) as f:
                    obj = json.load(f)
            except json.decoder.JSONDecodeError:
                raise click.BadParameter(
                    'Request does not contain valid json.',
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
        collection of fake subscriptions (the all_subs fixture).
        After we refactor we will change to mocking the API.

        """
        # Begin fake subscriptions service. Note that the Subscriptions
        # API will report missing keys differently, but the Python API
        # *will* raise PlanetError like this.
        missing_keys = {'name', 'delivery', 'source'} - request.keys()
        if missing_keys:
            raise PlanetError(
                f"Request lacks required members: {missing_keys!r}")

        # Update the request with an id.
        sub = dict(**request, id='42')
        # End fake subscriptions service. After we refactor we will get
        # the "sub" from a method in planet.clients.subscriptions (which
        # doesn't exist yet).

        echo_json(sub, pretty)

    cli.main.add_command(subscriptions)
    # End of the command code.

    # This subscription request lacks the required "delivery" and
    # "source" members.
    sub = {'name': 'lol'}

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'create', '-'],
        input=json.dumps(sub),
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)
    assert result.exit_code == 1  # failure.
    assert "Request lacks required members" in result.output
