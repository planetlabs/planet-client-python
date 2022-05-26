"""Tests of the Subscriptions CLI (aka planet-subscriptions)

There are 6 subscriptions commands:

planet subscriptions list
planet subscriptions describe
planet subscriptions results
planet subscriptions create
planet subscriptions update
planet subscriptions cancel

"""

import json

from click.testing import CliRunner
import pytest

from planet.cli import cli
import planet.cli.subscriptions
from planet.cli.subscriptions import _count_fake_subs


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
def test_subscriptions_list_options(options, expected_count, monkeypatch):
    """Prints the expected sequence of subscriptions."""

    monkeypatch.setattr(planet.cli.subscriptions,
                        '_fake_subs',
                        [{
                            'id': str(i), 'status': 'created'
                        } for i in range(101)])

    # While developing it is handy to have click's command invoker
    # *not* catch exceptions, so we can use the pytest --pdb option.
    result = CliRunner().invoke(cli.main,
                                args=['subscriptions', 'list'] + options,
                                catch_exceptions=False)
    assert result.exit_code == 0  # success.

    # For a start, counting the number of "id" strings in the output
    # tells us how many subscription JSONs were printed, pretty or not.
    assert result.output.count('"id"') == expected_count


def test_subscriptions_create_failure(monkeypatch):
    """An invalid subscription request fails to create a new subscription."""

    monkeypatch.setattr(planet.cli.subscriptions, '_fake_subs', [])

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
    assert _count_fake_subs() == 0


def test_subscriptions_create_success(monkeypatch):
    """An valid subscription request succeeds in creating a new subscription."""

    monkeypatch.setattr(planet.cli.subscriptions, '_fake_subs', [])

    # This subscription request has the members required by our fake API.
    # It must be updated when we begin to test against a more strict
    # imitation of the Planet Subscriptions API.
    sub = {'name': 'lol', 'delivery': True, 'source': 'wut'}

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

    assert result.exit_code == 0  # success.
    assert "Request lacks required members" not in result.output
    assert json.loads(result.output)['id'] == '42'
    assert _count_fake_subs() == 1
