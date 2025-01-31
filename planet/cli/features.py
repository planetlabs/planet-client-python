from contextlib import asynccontextmanager
import json
import click
from click.exceptions import ClickException

from planet.cli.io import echo_json
from planet.clients.features import FeaturesClient

from .cmds import coro, translate_exceptions
from .options import pretty
from .session import CliSession


@asynccontextmanager
async def features_client(ctx):
    async with CliSession() as sess:
        cl = FeaturesClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Features API URL.')
def features(ctx, base_url):
    """Commands for interacting with Features API"""
    ctx.obj['BASE_URL'] = base_url


@features.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.option("-t",
              "--title",
              required=True,
              help="a title for the collection")
@click.option("-d",
              "--description",
              "--desc",
              required=False,
              help="a description for the collection")
@pretty
async def collection_create(ctx, title, description, pretty):
    """Create a new Features API collection.

    Example:

    \b
    planet features collection-create \\
      --title "new collection" \\
      --desc "my new collection"
    """
    async with features_client(ctx) as cl:
        col = await cl.create_collection(title, description)
        echo_json(col, pretty)


@features.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@pretty
async def collections_list(ctx, pretty):
    """List Features API collections

    Example:

    planet features collections-list
    """
    async with features_client(ctx) as cl:
        results = cl.list_collections()
        echo_json([c async for c in results], pretty)


@features.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("collection_id", required=True)
@pretty
async def collection_get(ctx, collection_id, pretty):
    """List Features API collections

    Example:

    planet features collection-get
    """
    async with features_client(ctx) as cl:
        result = await cl.get_collection(collection_id)
        echo_json(result, pretty)


@features.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("collection_id", required=True)
@pretty
async def items_list(ctx, collection_id, pretty):
    """List features in a Features API collection

    Example:

    planet features items-list my-collection-123
    """
    async with features_client(ctx) as cl:
        results = cl.list_features(collection_id)
        echo_json([f async for f in results], pretty)


@features.command()  # type: ignore
@click.pass_context
@translate_exceptions
@coro
@click.argument("collection_id", required=True)
@click.argument("filename", required=True)
@pretty
async def item_add(ctx, collection_id, filename, pretty):
    """Add features from a geojson file to a collection

    Example:

    planet features item-add my-collection-123 ./my_geom.geojson
    """
    async with features_client(ctx) as cl:
        with open(filename) as data:
            try:
                res = await cl.add_features(collection_id, json.load(data))
            except json.decoder.JSONDecodeError:
                raise ClickException(
                    "Only JSON (.json, .geojson) files are supported in the CLI. Please use https://planet.com/features to upload other files."
                )

    echo_json(res, pretty)
