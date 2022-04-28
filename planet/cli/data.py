"""The Planet Data CLI."""

import json
from typing import AsyncIterator, List

import click

from .cmds import coro, translate_exceptions
from .io import echo_json

# Parameter callbacks are what we use to validate and transform the
# values of arguments and options. On the command line, everything is
# a string, but we want to transform to natural Python types as soon as
# possible.


def parse_item_types(ctx, param, value) -> list:
    """Turn a string of comma-separated names into a list of names."""
    # Note: we could also normalize case and validate the names against
    # our schema here.
    return [part.strip() for part in (value or "").split(",")]


def parse_filter(ctx, param, value) -> dict:
    """Turn filter JSON into a dict."""
    return json.loads(value)


@click.group()
@click.pass_context
def data(ctx):
    """A group of commands for interacting with the Data API."""


# TODO: filter().


@data.command()
@translate_exceptions
# Our CLI command functions are async functions. They need an event
# loop to be executed. The coro decorator provides that event loop.
@coro
# The command has two positional arguments. ITEM_TYPES comes first.
@click.argument("item_types", callback=parse_item_types)
@click.argument("filter", callback=parse_filter)
# The command has three options.
@click.option("--limit",
              type=int,
              default=100,
              help="Maximum number of results to return.")
@click.option("--name", help="Name for the saved search.")
@click.option("--pretty", is_flag=True, help="Pretty print output.")
# This decorator gives our function a context (named "ctx") that may
# contain parameters set by the "planet data" command group, like
# "planet --quiet data" or "planet --verbosity=debug data".
@click.pass_context
async def search_quick(ctx,
                       item_types: List[str],
                       filter: dict,
                       limit: int,
                       pretty: bool,
                       name: str):
    """Execute a structured item search and print results.

    Results are represented as a sequence of GeoJSON features.

    """

    # Note: API tokens will be found in "ctx". They are unused in this
    # example.
    #
    # The Planet Data client will return a stream of GeoJSON
    # Feature-like dicts (aka an "iterator"). The search_quick function
    # will iterate over the features, encode them as JSON, and echo
    # them. We simulate that here.
    async def example_client(item_types,
                             filter,
                             limit=0,
                             name=None) -> AsyncIterator[dict]:
        """This is a placeholder.

        We'll delete this and use the real method from
        planet.clients.data when it is available.

        """
        # Note: we re-emit the input item types and filter to help us
        # sanity check during early sprints.
        for feature in item_types:
            yield dict(item_type=feature)

        yield dict(filter=filter)

    # CLI functions raise ClickException when any kind of intentionally
    # raised PlanetError occurs. We *don't* handle other errors now
    # because those will be caused by bugs in our code and we want them
    # raw and unfiltered.
    async for feature in example_client(item_types,
                                        filter,
                                        limit=limit,
                                        name=name):
        echo_json(feature, pretty=pretty)


# TODO: search_create()".
# TODO: search_update()".
# TODO: search_delete()".
# TODO: search_run()".
# TODO: item_get()".
# TODO: asset_activate()".
# TODO: asset_wait()".
# TODO: asset_download()".
# TODO: search_create()".
# TODO: stats()".
