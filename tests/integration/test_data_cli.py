"""Tests of the Data CLI."""

from click.testing import CliRunner
import pytest

from planet.cli import cli


def test_data_command_registered():
    """planet-data command prints help and usage message."""
    result = CliRunner().invoke(cli.main, ["data", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "search-quick" in result.output
    # Add other sub-commands here.


# TODO: basic test for "planet data filter".

# We expect this test to fail now. When the Data API client is
# available, we will remove the xfail marker and work to get this test,
# or a better version, to pass.
@pytest.mark.xfail(reason="Data client not yet implemented")
def test_search_quick():
    """planet data search-quick prints 1 GeoJSON Feature."""
    result = CliRunner().invoke(
        cli.main,
        # When testing, we "explode" our command and its parameters
        # into a list to make parameterization more clear.
        [
            "data",
            "search-quick",
            # To keep yapf from putting option name and value on
            # different lines, use a "=".
            "--limit=10",
            "--name=test",
            "--pretty",
            "lol,wut",
            "{}"
        ])
    assert result.exit_code == 0
    assert "Feature" in result.output


# TODO: basic test for "planet data search-create".
# TODO: basic test for "planet data search-update".
# TODO: basic test for "planet data search-delete".
# TODO: basic test for "planet data search-run".
# TODO: basic test for "planet data item-get".
# TODO: basic test for "planet data asset-activate".
# TODO: basic test for "planet data asset-wait".
# TODO: basic test for "planet data asset-download".
# TODO: basic test for "planet data search-create".
# TODO: basic test for "planet data stats".
