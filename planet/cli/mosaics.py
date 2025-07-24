import asyncio
from contextlib import asynccontextmanager

import click

from planet.cli.cmds import command
from planet.cli.io import echo_json
from planet.cli.session import CliSession
from planet.cli.types import BoundingBox, DateTime, Geometry
from planet.cli.validators import check_geom
from planet.clients.mosaics import MosaicsClient


@asynccontextmanager
async def client(ctx):
    async with CliSession() as sess:
        cl = MosaicsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


include_links = click.option("--links",
                             is_flag=True,
                             help=("If enabled, include API links"))

name_contains = click.option(
    "--name-contains",
    type=str,
    help=("Match if the name contains text, case-insensitive"))

bbox = click.option('--bbox',
                    type=BoundingBox(),
                    help=("Region to download as comma-delimited strings: "
                          " lon_min,lat_min,lon_max,lat_max"))

interval = click.option("--interval",
                        type=str,
                        help=("Match this interval, e.g. 1 mon"))

acquired_gt = click.option("--acquired_gt",
                           type=DateTime(),
                           help=("Imagery acquisition after than this date"))

acquired_lt = click.option("--acquired_lt",
                           type=DateTime(),
                           help=("Imagery acquisition before than this date"))

geometry = click.option('--geometry',
                        type=Geometry(),
                        callback=check_geom,
                        help=("A geojson geometry to search with. "
                              "Can be a string, filename, or - for stdin."))


def _strip_links(resource):
    if isinstance(resource, dict):
        resource.pop("_links", None)
    return resource


async def _output(result, pretty, include_links=False):
    if asyncio.iscoroutine(result):
        result = await result
        if not include_links:
            _strip_links(result)
        echo_json(result, pretty)
    else:
        results = [_strip_links(r) async for r in result]
        echo_json(results, pretty)


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Mosaics API URL.')
def mosaics(ctx, base_url):
    """Commands for interacting with the Mosaics API"""
    ctx.obj['BASE_URL'] = base_url


@mosaics.group()  # type: ignore
def series():
    """Commands for interacting with Mosaic Series through the Mosaics API"""


@command(mosaics, name="contributions")
@click.argument("name_or_id")
@click.argument("quad")
async def quad_contributions(ctx, name_or_id, quad, pretty):
    '''Get contributing scenes for a quad in a mosaic specified by name or ID

    Example:

    planet mosaics contribution global_monthly_2025_04_mosaic 575-1300
    '''
    async with client(ctx) as cl:
        item = await cl.get_quad(name_or_id, quad)
        await _output(cl.get_quad_contributions(item), pretty)


@command(mosaics, name="info")
@click.argument("name_or_id", required=True)
@include_links
async def mosaic_info(ctx, name_or_id, pretty, links):
    """Get information for a mosaic specified by name or ID

    Example:

    planet mosaics info global_monthly_2025_04_mosaic
    """
    async with client(ctx) as cl:
        await _output(cl.get_mosaic(name_or_id), pretty, links)


@command(mosaics, name="list")
@name_contains
@interval
@acquired_gt
@acquired_lt
@include_links
async def mosaics_list(ctx,
                       name_contains,
                       interval,
                       acquired_gt,
                       acquired_lt,
                       pretty,
                       links):
    """List information for all available mosaics

    Example:

    planet mosaics list --name-contains global_monthly
    """
    async with client(ctx) as cl:
        await _output(
            cl.list_mosaics(name_contains=name_contains,
                            interval=interval,
                            acquired_gt=acquired_gt,
                            acquired_lt=acquired_lt),
            pretty,
            links)


@command(series, name="info")
@click.argument("name_or_id", required=True)
@include_links
async def series_info(ctx, name_or_id, pretty, links):
    """Get information for a series specified by name or ID

    Example:

    planet series info "Global Quarterly"
    """
    async with client(ctx) as cl:
        await _output(cl.get_series(name_or_id), pretty, links)


@command(series, name="list")
@name_contains
@interval
@acquired_gt
@acquired_lt
@include_links
async def series_list(ctx,
                      name_contains,
                      interval,
                      acquired_gt,
                      acquired_lt,
                      pretty,
                      links):
    """List information for available series

    Example:

    planet mosaics series list --name-contains=Global
    """
    async with client(ctx) as cl:
        await _output(
            cl.list_series(
                name_contains=name_contains,
                interval=interval,
                acquired_gt=acquired_gt,
                acquired_lt=acquired_lt,
            ),
            pretty,
            links)


@command(series, name="list-mosaics")
@click.argument("name_or_id", required=True)
@click.option("--latest",
              is_flag=True,
              help=("Get the latest mosaic in the series"))
@acquired_gt
@acquired_lt
@include_links
async def list_series_mosaics(ctx,
                              name_or_id,
                              acquired_gt,
                              acquired_lt,
                              latest,
                              pretty,
                              links):
    """List mosaics in a series specified by name or ID

    Example:

    planet mosaics series list-mosaics global_monthly_2025_04_mosaic
    """
    async with client(ctx) as cl:
        await _output(
            cl.list_series_mosaics(name_or_id,
                                   acquired_gt=acquired_gt,
                                   acquired_lt=acquired_lt,
                                   latest=latest),
            pretty,
            links)


@command(mosaics, name="search")
@click.argument("name_or_id", required=True)
@bbox
@geometry
@click.option("--summary",
              is_flag=True,
              help=("Get a count of how many quads would be returned"))
@include_links
async def list_quads(ctx, name_or_id, bbox, geometry, summary, pretty, links):
    """Search quads in a mosaic specified by name or ID

    Example:

    planet mosaics search global_monthly_2025_04_mosaic --bbox -100,40,-100,41
    """
    async with client(ctx) as cl:
        if summary:
            result = cl.summarize_quads(name_or_id,
                                        bbox=bbox,
                                        geometry=geometry)
        else:
            result = cl.list_quads(name_or_id,
                                   minimal=False,
                                   bbox=bbox,
                                   geometry=geometry)
        await _output(result, pretty, links)


@command(mosaics, name="download")
@click.argument("name_or_id", required=True)
@click.option('--output-dir',
              help=('Directory for file download. Defaults to mosaic name'),
              type=click.Path(exists=True,
                              resolve_path=True,
                              writable=True,
                              file_okay=False))
@bbox
@geometry
async def download(ctx, name_or_id, output_dir, bbox, geometry, **kwargs):
    """Download quads from a mosaic by name or ID

    Example:

    planet mosaics search global_monthly_2025_04_mosaic --bbox -100,40,-100,41
    """
    quiet = ctx.obj['QUIET']
    async with client(ctx) as cl:
        await cl.download_quads(name_or_id,
                                bbox=bbox,
                                geometry=geometry,
                                directory=output_dir,
                                progress_bar=not quiet)
