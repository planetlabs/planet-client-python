"""Tests of the Subscriptions CLI (aka planet-subscriptions)

There are 6 subscriptions commands:

[x] planet subscriptions list
[x] planet subscriptions describe
[x] planet subscriptions results
[x] planet subscriptions create
[x] planet subscriptions update
[x] planet subscriptions cancel

TODO: tests for 3 options of the planet-subscriptions-results command.

"""

import json

from click.testing import CliRunner
import pytest

from planet.cli import cli
import planet.cli.subscriptions

from test_subscriptions_api import (api_mock,
                                    failing_api_mock,
                                    modify_api_mock,
                                    sub_api_mock)


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
@api_mock
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_list_options(options, expected_count):
    """Prints the expected sequence of subscriptions."""
    # While developing it is handy to have click's command invoker
    # *not* catch exceptions, so we can use the pytest --pdb option.
    result = CliRunner().invoke(cli.main,
                                args=['subscriptions', 'list'] + options,
                                catch_exceptions=False)
    assert result.exit_code == 0  # success.

    # For a start, counting the number of "id" strings in the output
    # tells us how many subscription JSONs were printed, pretty or not.
    assert result.output.count('"id"') == expected_count


@failing_api_mock
def test_subscriptions_create_failure():
    """An invalid subscription request fails to create a new subscription."""

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
    assert "Error:" in result.output


# This subscription request has the members required by our fake API.
# It must be updated when we begin to test against a more strict
# imitation of the Planet Subscriptions API.
GOOD_SUB_REQUEST = {'name': 'lol', 'delivery': True, 'source': 'wut'}


@pytest.mark.parametrize('cmd_arg, runner_input',
                         [('-', json.dumps(GOOD_SUB_REQUEST)),
                          (json.dumps(GOOD_SUB_REQUEST), None)])
@modify_api_mock
def test_subscriptions_create_success(cmd_arg, runner_input):
    """Subscriptions creation succeeds with a valid subscription request."""

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


# Invalid JSON.
BAD_SUB_REQUEST = '{0: "lolwut"}'


@pytest.mark.parametrize('cmd_arg, runner_input', [('-', BAD_SUB_REQUEST),
                                                   (BAD_SUB_REQUEST, None)])
def test_subscriptions_bad_request(cmd_arg, runner_input):
    """Short circuit and print help message if request is bad."""

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 2  # bad parameter.
    assert "Request does not contain valid json" in result.output


@failing_api_mock
def test_subscriptions_cancel_failure():
    """Cancel command exits gracefully from an API error."""

    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'cancel', '42'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@modify_api_mock
def test_subscriptions_cancel_success():
    """Cancel command succeeds."""
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'cancel', '42'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


@failing_api_mock
def test_subscriptions_update_failure():
    """Update command exits gracefully from an API error."""
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'update', '42', json.dumps(GOOD_SUB_REQUEST)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@modify_api_mock
def test_subscriptions_update_success():
    """Update command succeeds."""
    request = GOOD_SUB_REQUEST.copy()
    request['name'] = 'new_name'

    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'update', '42', json.dumps(request)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['name'] == 'new_name'


@failing_api_mock
def test_subscriptions_describe_failure():
    """Describe command exits gracefully from an API error."""
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'describe', '42'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@sub_api_mock
def test_subscriptions_describe_success():
    """Describe command succeeds."""
    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'describe', '42'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['id'] == '42'


def test_subscriptions_results_failure(monkeypatch):
    """Results command exits gracefully from an API error."""

    monkeypatch.setattr(planet.clients.subscriptions, '_fake_sub_results', {})

    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'results', '42'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.
    assert "Subscription failure." in result.output


@pytest.mark.parametrize('options,expected_count',
                         [(['--status=created'], 100), ([], 100),
                          (['--limit=1', '--status=created'], 1),
                          (['--limit=2', '--pretty', '--status=created'], 2),
                          (['--limit=1', '--status=queued'], 0)])
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_results_success(options, expected_count, monkeypatch):
    """Describe command succeeds."""

    monkeypatch.setattr(
        planet.clients.subscriptions,
        '_fake_sub_results',
        {'42': [{
            'id': f'r{i}', 'status': 'created'
        } for i in range(101)]})

    result = CliRunner().invoke(
        cli.main,
        args=['subscriptions', 'results', '42'] + options,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert result.output.count('"id"') == expected_count
