"""The Planet Data CLI."""

import json
from typing import AsyncIterator, List
from contextlib import asynccontextmanager
import re

import click
import planet
from planet import DataClient, Session
from os import path

from .cmds import coro, translate_exceptions
from .io import echo_json

pretty = click.option('--pretty', is_flag=True, help='Pretty-print output.')


@asynccontextmanager
async def data_client(ctx):
    auth = ctx.obj['AUTH']
    base_url = ctx.obj['BASE_URL']
    async with Session(auth=auth) as sess:
        cl = DataClient(sess, base_url=base_url)
        yield cl


# Parameter callbacks are what we use to validate and transform the
# values of arguments and options. On the command line, everything is
# a string, but we want to transform to natural Python types as soon as
# possible.


@click.pass_context
def parse_item_types(ctx, param, value: str) -> List[str]:
    """Turn a string of comma-separated names into a list of names."""
    # Note: we could also normalize case and validate the names against
    # our schema here.
    return [part.strip() for part in value.split(",")]


@click.pass_context
def parse_filter(ctx, param, value: str) -> dict:
    """Turn filter JSON into a dict."""
    return json.loads(value)


@click.group()
@click.pass_context
def data(ctx):
    """A group of commands for interacting with the Data API."""


# TODO: filter().

# @data.command()
# @translate_exceptions
# # Our CLI command functions are async functions. They need an event
# # loop to be executed. The coro decorator provides that event loop.
# @coro
# # The command has two positional arguments. ITEM_TYPES comes first.
# # By default these are required and will evaluate to str type.
# @click.argument("item_types", callback=parse_item_types)
# @click.argument("filter", callback=parse_filter)
# # The command has three options.
# @click.option("--limit",
#               type=int,
#               default=100,
#               help="Maximum number of results to return.")
# @click.option("--name", help="Name for the saved search.")
# @click.option("--pretty", is_flag=True, help="Pretty print output.")
# # This decorator gives our function a context (named "ctx") that may
# # contain parameters set by the "planet data" command group, like
# # "planet --quiet data" or "planet --verbosity=debug data".
# @click.pass_context
# async def search_quick(ctx,
#                        item_types: List[str],
#                        filter: dict,
#                        limit: int,
#                        pretty: bool,
#                        name: str):
#     """Execute a structured item search and print results.

#     Results are represented as a sequence of GeoJSON features.

#     """

#     # Note: API tokens will be found in "ctx". They are unused in this
#     # example.
#     #
#     # The Planet Data client will return a stream of GeoJSON
#     # Feature-like dicts (aka an "iterator"). The search_quick function
#     # will iterate over the features, encode them as JSON, and echo
#     # them. We simulate that here.
#     async def example_client(item_types,
#                              filter,
#                              limit=0,
#                              name=None) -> AsyncIterator[dict]:
#         """This is a placeholder.

#         We'll delete this and use the real method from
#         planet.clients.data when it is available.

#         """
#         # Note: we re-emit the input item types and filter to help us
#         # sanity check during early sprints.
#         for feature in item_types:
#             yield dict(item_type=feature)

#         yield dict(filter=filter)

#     # CLI functions raise ClickException when any kind of intentionally
#     # raised PlanetError occurs. We *don't* handle other errors now
#     # because those will be caused by bugs in our code and we want them
#     # raw and unfiltered.
#     async for feature in example_client(item_types,
#                                         filter,
#                                         limit=limit,
#                                         name=name):
#         echo_json(feature, pretty=pretty)


def _split(value):
    '''return input split on any whitespace or comma'''
    return re.split(r'\s+|,', value)


def read(value, split=False):
    '''Get the value of an option interpreting as a file implicitly or
    explicitly and falling back to the value if not explicitly specified.
    If the value is '-', then stdin will be read and returned as
    the value. Finally, if a file exists with the provided value, that
    file will be read. Otherwise, the value will be returned.
    '''
    v = str(value)
    retval = value
    if v == '-':
        fname = '-' if v == '-' else v[1:]
        with click.open_file(fname) as fp:
            if not fp.isatty():
                retval = fp.read()
            else:
                retval = None
    elif path.exists(v) and path.isfile(v):
        with click.open_file(v) as fp:
            retval = fp.read()
    if retval and split and type(retval) != tuple:
        retval = _split(retval.strip())
    return retval


@data.command()
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument("item_types", callback=parse_item_types)
@click.argument("filter", callback=parse_filter)
@click.option('--name',
              type=str,
              default=False,
              help=('Name of the saved search.'))
@click.option('--limit',
              type=int,
              default=100,
              help='Maximum number of results to return. Defaults to 100.')
async def search_quick(ctx, item_types, filter, name, limit, pretty):
    """Execute a structured item search.
    Quick searches are stored for approximately 30 days and the --name parameter will be
    applied to the stored quick search. \n

    Arguments: \n
    ITEM_TYPES - string. Comma-separated item type identifier(s). \n
    FILTER - string. A full JSON description of search criteria. Supports file and stdin. \n

    Output:
    A series of GeoJSON descriptions for each of the returned items.

    """
    async with data_client(ctx) as cl:
        data = await cl.quick_search(name=name,
                                     item_types=item_types,
                                     search_filter=filter,
                                     limit=limit,
                                     sort=None)
    echo_json(data, pretty)


@data.command()
@click.pass_context
@translate_exceptions
@coro
@click.option('--daily_email',
              is_flag=True,
              default=False,
              help=('Send a daily email when new results are added.'))
@pretty
async def search_create(ctx, name, item_types, filter, pretty, daily_email):
    """Create a new saved structured item search. \n
    Arguments: \n
    NAME - string. The name to give the saved search. \n
    ITEM_TYPES - string. Comma-separated item type identifier(s). \n
    FILTER - string. A full JSON description of search criteria. Supports file and stdin.
    """
    async with data_client(ctx) as cl:
        data = await cl.create_search(name=name,
                                      item_types=item_types,
                                      search_filter=filter,
                                      enable_email=daily_email)

    echo_json(data, pretty)


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
