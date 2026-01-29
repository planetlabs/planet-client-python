"""Catalog CLI"""
from contextlib import asynccontextmanager

import click

from . import types
from .cmds import coro, translate_exceptions
from .io import echo_json
from .options import pretty
from .session import CliSession
from planet.clients.catalog import CatalogClient

@asynccontextmanager
async def catalog_client(ctx):
    async with CliSession(ctx) as sess:
        cl = CatalogClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl

@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Catalog API URL.')
def catalog(ctx, base_url):
    """Commands for interacting with the Catalog API"""
    ctx.obj['BASE_URL'] = base_url

@catalog.command(name="info")  # type: ignore
@pretty
@click.pass_context
@translate_exceptions
@coro
async def get_info_cmd(ctx, pretty):
    async with catalog_client(ctx) as client:
        info = await client.get_info()
        echo_json(info, pretty)

@catalog.command(name="conformance")  # type: ignore
@pretty
@click.pass_context
@translate_exceptions
@coro
async def get_conformance_cmd(ctx, pretty):
    async with catalog_client(ctx) as client:
        conformance = await client.get_conformance()
        echo_json(conformance, pretty)

@catalog.command(name="collections")  # type: ignore
@pretty
@click.pass_context
@translate_exceptions
@coro
async def get_collections_cmd(ctx, pretty):
    async with catalog_client(ctx) as client:
        collections = await client.get_collections()
        echo_json(collections, pretty)