"""The Planet Data CLI."""

import json
from typing import List
from contextlib import asynccontextmanager

import click
import planet
from planet import DataClient, Session

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


@click.group()
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Orders API URL.')
def data(ctx, base_url):
    '''Commands for interacting with the Orders API'''
    ctx.obj['AUTH'] = planet.Auth.from_file()
    ctx.obj['BASE_URL'] = base_url


def parse_item_types(ctx, param, value: str) -> List[str]:
    """Turn a string of comma-separated names into a list of names."""
    # Note: we could also normalize case and validate the names against
    # our schema here.
    return [part.strip() for part in value.split(",")]


def parse_filter(ctx, param, value: str) -> dict:
    """Turn filter JSON into a dict."""
    # read filter using raw json
    if value.startswith('{'):
        try:
            json_value = json.loads(value)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Filter does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
        if json_value == {}:
            raise click.BadParameter('Filter is empty.', ctx=ctx, param=param)
        return json_value
    # read filter using click pipe option
    else:
        try:
            with click.open_file(value) as f:
                json_value = json.load(f)
        except json.decoder.JSONDecodeError:
            raise click.BadParameter('Filter does not contain valid json.',
                                     ctx=ctx,
                                     param=param)
        return json_value


# TODO: filter().


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
    """This function executes a structured item search using the item_types,
    and json filter specified (using file or stdin).
    Quick searches are stored for approximately 30 days and the --name
    parameter will be applied to the stored quick search. This function
    outputs a series of GeoJSON descriptions, one for each of the returned items.
    The limit on the number of output items can be controlled using the "--limit" option, which defaults to 100. If "--limit" is set to zero, no limit is applied and all results (a potentially large number) are returned. The output can also be optionally pretty-printed
    using "--pretty".
    """
    async with data_client(ctx) as cl:
        items = await cl.quick_search(name=name,
                                      item_types=item_types,
                                      search_filter=filter,
                                      limit=limit,
                                      sort=None)
        async for item in items:
            echo_json(item, pretty)


@data.command()
@click.pass_context
@translate_exceptions
@coro
@pretty
@click.argument('name')
@click.argument("item_types", callback=parse_item_types)
@click.argument("filter", callback=parse_filter)
@click.option('--daily_email',
              is_flag=True,
              help='Send a daily email when new results are added.')
async def search_create(ctx, name, item_types, filter, daily_email, pretty):
    """ This function creates a new saved structured item search, using the
    name of the search, item_types, and json filter specified (using file or
    stdin). If specified, the "--daily_email" option enables users to recieve
    an email when new results are available each day. This function outputs a
    full JSON description of the created search. The output can also be
    optionally pretty-printed using "--pretty".

    """
    async with data_client(ctx) as cl:
        items = await cl.create_search(name=name,
                                       item_types=item_types,
                                       search_filter=filter,
                                       enable_email=daily_email)
        echo_json(items, pretty)


# TODO: search_update()".
# TODO: search_delete()".
# TODO: search_run()".
# TODO: item_get()".
# TODO: asset_activate()".
# TODO: asset_wait()".
# TODO: asset_download()".
# TODO: stats()".
